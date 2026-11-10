import asyncio
import json
import os
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .graph import run_graph
from .models import (
    GraphState,
    RequirementsRequest,
    ResearchRequest,
    Session,
    SessionCreate,
    SessionStatus,
    SourceCreate,
)
from .services.citations import build_research_summary
from .services.critic import critic_decision
from .services.discovery import generate_discovery
from .services.evaluator import evaluate_requirements
from .services.requirements_agent import build_requirements
from .services.observability import request_metrics
from .services.persistence import PersistenceError, Repository
from .services.redaction import redact_pii
from .services.risk import assess_opportunity_risk
from .services.retrieval import evidence_store

app = FastAPI(title="ConsultAI", version="0.1.0")
_sessions: dict[UUID, GraphState] = {}
_repository = Repository() if os.getenv("CONSULTAI_STORAGE") == "postgres" else None
if _repository is not None:
    evidence_store.repository = _repository
app.middleware("http")(request_metrics)


@app.middleware("http")
async def require_api_key(request: Request, call_next):
    from .config import get_settings

    configured_key = get_settings().api_key
    if configured_key and request.url.path not in {"/health", "/docs", "/openapi.json", "/redoc"}:
        if request.headers.get("X-API-Key") != configured_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "consultai"}


@app.post("/api/sessions", status_code=201)
def create_session(payload: SessionCreate) -> dict:
    redaction = redact_pii(payload.process_description)
    session = Session(vertical=payload.vertical, status=SessionStatus.RUNNING)
    state = GraphState(
        session=session,
        process_description=redaction.text,
        redacted_description=redaction.text,
        redaction_count=redaction.count,
        redaction_entity_types=list(redaction.entity_types),
    )
    _sessions[session.id] = state
    if _repository is not None:
        _repository.save_session(state)
    return {"session": session, "status_url": f"/api/sessions/{session.id}"}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: UUID) -> dict:
    state = _sessions.get(session_id)
    if state is None and _repository is not None:
        state = _repository.get_session(session_id)
        if state is not None:
            _sessions[session_id] = state
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": state.session, "events": state.events, "result": state.model_dump()}


@app.post("/api/sessions/{session_id}/run")
def run_session(session_id: UUID) -> dict:
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _sessions[session_id] = run_graph(state)
    if _repository is not None:
        _repository.save_session(_sessions[session_id])
        _repository.checkpoint(_sessions[session_id])
    return get_session(session_id)


@app.post("/api/discovery")
def discovery(payload: SessionCreate) -> dict:
    result = generate_discovery(payload.process_description, payload.vertical)
    return result.model_dump(mode="json")


@app.post("/api/requirements")
def requirements(payload: RequirementsRequest) -> dict:
    result = build_requirements(payload.process_description, payload.discovery_answers)
    return result.model_dump(mode="json")


@app.post("/api/sessions/{session_id}/sources", status_code=201)
def add_source(session_id: UUID, payload: SourceCreate) -> dict:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    redaction = redact_pii(payload.text)
    safe_payload = payload.model_copy(update={"text": redaction.text})
    document = evidence_store.add(session_id, safe_payload)
    result = document.model_dump(mode="json")
    result["redaction_count"] = redaction.count
    result["redaction_entity_types"] = list(redaction.entity_types)
    return result


@app.post("/api/sessions/{session_id}/retrieve")
def retrieve_sources(session_id: UUID, payload: ResearchRequest) -> dict:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    result = evidence_store.corrective_retrieve(
        session_id,
        payload.query,
        min_score=payload.min_support_score,
    )
    return result.model_dump(mode="json")


@app.post("/api/sessions/{session_id}/research")
def research(session_id: UUID, payload: ResearchRequest) -> dict:
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    retrieval = evidence_store.corrective_retrieve(
        session_id,
        payload.query,
        min_score=payload.min_support_score,
    )
    return build_research_summary(payload.query, retrieval.hits).model_dump(mode="json")


@app.post("/api/evaluate")
def evaluate(payload: RequirementsRequest) -> dict:
    requirements_doc = build_requirements(payload.process_description, payload.discovery_answers)
    result = evaluate_requirements(requirements_doc.model_dump(mode="json"))
    return result


@app.post("/api/critic")
def critic(payload: RequirementsRequest) -> dict:
    requirements_doc = build_requirements(payload.process_description, payload.discovery_answers)
    evaluation = evaluate_requirements(requirements_doc.model_dump(mode="json"))
    return critic_decision(evaluation)


@app.post("/api/risk-check")
def risk_check(payload: dict[str, object]) -> dict:
    return assess_opportunity_risk(payload)


@app.get("/api/sessions/{session_id}/stream")
async def stream_session(session_id: UUID) -> StreamingResponse:
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def events() -> AsyncIterator[str]:
        for event in state.events:
            yield f"data: {json.dumps(event.model_dump(mode='json'))}\n\n"
            await asyncio.sleep(0)
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
