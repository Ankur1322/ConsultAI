import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

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
from .services.discovery import generate_discovery
from .services.requirements_agent import build_requirements
from .services.retrieval import evidence_store

app = FastAPI(title="ConsultAI", version="0.1.0")
_sessions: dict[UUID, GraphState] = {}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "consultai"}


@app.post("/api/sessions", status_code=201)
def create_session(payload: SessionCreate) -> dict:
    session = Session(vertical=payload.vertical, status=SessionStatus.RUNNING)
    state = GraphState(session=session, process_description=payload.process_description)
    _sessions[session.id] = state
    return {"session": session, "status_url": f"/api/sessions/{session.id}"}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: UUID) -> dict:
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": state.session, "events": state.events, "result": state.model_dump()}


@app.post("/api/sessions/{session_id}/run")
def run_session(session_id: UUID) -> dict:
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _sessions[session_id] = run_graph(state)
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
    return evidence_store.add(session_id, payload).model_dump(mode="json")


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
