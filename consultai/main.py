import asyncio
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .graph import build_graph, resume_graph, run_graph
from .models import (
    GraphState,
    LoginRequest,
    RegisterRequest,
    ReviewDecision,
    RequirementsRequest,
    ResearchRequest,
    Session,
    SessionCreate,
    SessionStatus,
    SourceCreate,
)
from .services.citations import build_research_summary
from .services.auth import (
    AuthenticatedUser,
    auth_enabled,
    hash_password,
    issue_token,
    new_identity,
    verify_password,
)
from .services.critic import critic_decision
from .services.discovery import generate_discovery
from .services.evaluator import evaluate_requirements
from .services.requirements_agent import build_requirements
from .services.observability import metrics_snapshot, request_metrics, increment
from .services.persistence import PersistenceError, Repository
from .services.redaction import redact_pii
from .services.risk import assess_opportunity_risk
from .services.retrieval import evidence_store

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create the official Postgres checkpointer only for durable deployments."""
    context_manager = None
    if os.getenv("CONSULTAI_STORAGE") == "postgres":
        from langgraph.checkpoint.postgres import PostgresSaver

        from .config import get_settings

        context_manager = PostgresSaver.from_conn_string(get_settings().database_url)
        checkpointer = context_manager.__enter__()
        checkpointer.setup()
        app.state.workflow = build_graph(checkpointer)
    else:
        app.state.workflow = build_graph()
    try:
        yield
    finally:
        if context_manager is not None:
            context_manager.__exit__(None, None, None)


app = FastAPI(title="ConsultAI", version="0.1.0", lifespan=lifespan)
_sessions: dict[UUID, GraphState] = {}
_repository = Repository() if os.getenv("CONSULTAI_STORAGE") == "postgres" else None
if _repository is not None:
    evidence_store.repository = _repository
app.middleware("http")(request_metrics)

def current_user(request: Request) -> AuthenticatedUser | None:
    if not auth_enabled():
        return None
    if _repository is None:
        raise HTTPException(status_code=503, detail="Persistent storage is required when authentication is enabled")
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    user = _repository.user_for_token(header[7:].strip())
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def workflow_for(request: Request):
    return getattr(request.app.state, "workflow", None)


@app.middleware("http")
async def require_api_key(request: Request, call_next):
    from .config import get_settings

    configured_key = get_settings().api_key
    public_paths = {"/health", "/docs", "/openapi.json", "/redoc", "/api/auth/register", "/api/auth/login"}
    if auth_enabled() and request.url.path not in public_paths:
        try:
            current_user(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    elif configured_key and request.url.path not in public_paths:
        if request.headers.get("X-API-Key") != configured_key:
            return JSONResponse(status_code=401, content={"detail": "Invalid or missing API key"})
    return await call_next(request)


@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest) -> dict[str, object]:
    if _repository is None:
        raise HTTPException(status_code=503, detail="Persistent storage is required for registration")
    user_id, generated_tenant = new_identity()
    user = AuthenticatedUser(user_id, payload.tenant_id or generated_tenant, payload.email, "owner")
    try:
        _repository.create_user(user, hash_password(payload.password))
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Email is already registered") from exc
    token, expires_at = issue_token(user.id)
    _repository.save_token(token, user.id, expires_at)
    _repository.audit(user, "auth.register")
    return {"access_token": token, "token_type": "bearer", "expires_at": expires_at, "tenant_id": user.tenant_id}


@app.post("/api/auth/login")
def login(payload: LoginRequest) -> dict[str, object]:
    if _repository is None:
        raise HTTPException(status_code=503, detail="Persistent storage is required for login")
    record = _repository.find_user(payload.email)
    if record is None or not verify_password(payload.password, record[1]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    user = record[0]
    token, expires_at = issue_token(user.id)
    _repository.save_token(token, user.id, expires_at)
    _repository.audit(user, "auth.login")
    return {"access_token": token, "token_type": "bearer", "expires_at": expires_at, "tenant_id": user.tenant_id}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "consultai"}


@app.get("/ready")
def ready() -> dict[str, str]:
    if _repository is not None:
        try:
            _repository.connect()
        except PersistenceError as exc:
            raise HTTPException(status_code=503, detail="PostgreSQL is not ready") from exc
    return {"status": "ready", "service": "consultai"}


@app.get("/metrics")
def metrics() -> dict[str, int | float]:
    return metrics_snapshot()


@app.post("/api/sessions", status_code=201)
def create_session(payload: SessionCreate, request: Request) -> dict:
    user = current_user(request)
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
        _repository.save_session(state, user)
        _repository.audit(user, "session.create", session.id)
    return {"session": session, "status_url": f"/api/sessions/{session.id}"}


@app.get("/api/sessions/{session_id}")
def get_session(session_id: UUID, request: Request) -> dict:
    user = current_user(request)
    state = _sessions.get(session_id)
    if state is not None and user and state.session.id != session_id:
        state = None
    if state is None and _repository is not None:
        state = _repository.get_session(session_id, user)
        if state is not None:
            _sessions[session_id] = state
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": state.session, "events": state.events, "result": state.model_dump()}


@app.post("/api/sessions/{session_id}/run")
def run_session(session_id: UUID, request: Request) -> dict:
    user = current_user(request)
    state = _sessions.get(session_id)
    if state is None and _repository is not None:
        state = _repository.get_session(session_id, user)
        if state is not None:
            _sessions[session_id] = state
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    _sessions[session_id] = run_graph(state, graph=workflow_for(request))
    if _repository is not None:
        _repository.save_session(_sessions[session_id], user)
    return get_session(session_id, request)


@app.post("/api/sessions/{session_id}/review")
def review_session(session_id: UUID, payload: ReviewDecision, request: Request) -> dict:
    user = current_user(request)
    state = _sessions.get(session_id)
    if state is None and _repository is not None:
        state = _repository.get_session(session_id, user)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")
    try:
        state = resume_graph(state, payload.approved, payload.comment, graph=workflow_for(request))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    _sessions[session_id] = state
    if _repository is not None:
        _repository.save_session(state, user)
        _repository.audit(user, "session.review", session_id)
    increment("human_reviews_total")
    return get_session(session_id, request)


@app.post("/api/discovery")
def discovery(payload: SessionCreate) -> dict:
    result = generate_discovery(payload.process_description, payload.vertical)
    return result.model_dump(mode="json")


@app.post("/api/requirements")
def requirements(payload: RequirementsRequest) -> dict:
    result = build_requirements(payload.process_description, payload.discovery_answers)
    return result.model_dump(mode="json")


@app.post("/api/sessions/{session_id}/sources", status_code=201)
def add_source(session_id: UUID, payload: SourceCreate, request: Request) -> dict:
    current_user(request)
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
def retrieve_sources(session_id: UUID, payload: ResearchRequest, request: Request) -> dict:
    current_user(request)
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    result = evidence_store.corrective_retrieve(
        session_id,
        payload.query,
        min_score=payload.min_support_score,
    )
    return result.model_dump(mode="json")


@app.post("/api/sessions/{session_id}/research")
def research(session_id: UUID, payload: ResearchRequest, request: Request) -> dict:
    current_user(request)
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
async def stream_session(session_id: UUID, request: Request) -> StreamingResponse:
    current_user(request)
    state = _sessions.get(session_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Session not found")

    async def events() -> AsyncIterator[str]:
        for event in state.events:
            yield f"data: {json.dumps(event.model_dump(mode='json'))}\n\n"
            await asyncio.sleep(0)
        yield "event: done\ndata: {}\n\n"

    return StreamingResponse(events(), media_type="text/event-stream")
