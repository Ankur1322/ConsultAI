from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class Vertical(StrEnum):
    INVOICE_TO_PAY = "invoice_to_pay"
    CUSTOMER_SUPPORT = "customer_support"


class SessionStatus(StrEnum):
    DRAFT = "draft"
    RUNNING = "running"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"


class Confidence(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SourceType(StrEnum):
    STATED = "stated"
    INFERRED = "inferred"


class DiscoveryQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    rationale: str
    required: bool = True


class DiscoveryResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    questions: list[DiscoveryQuestion] = Field(default_factory=list)
    missing_topics: list[str] = Field(default_factory=list)


class RequirementItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    text: str
    source_type: SourceType
    evidence: str | None = None
    confidence: Confidence
    acceptance_criterion: str | None = None


class RequirementsDoc(BaseModel):
    model_config = ConfigDict(extra="forbid")

    goals: list[RequirementItem] = Field(default_factory=list)
    functional: list[RequirementItem] = Field(default_factory=list)
    non_functional: list[RequirementItem] = Field(default_factory=list)
    assumptions: list[RequirementItem] = Field(default_factory=list)
    constraints: list[RequirementItem] = Field(default_factory=list)
    open_questions: list[RequirementItem] = Field(default_factory=list)


class ProcessNode(BaseModel):
    id: str
    label: str
    node_type: str = "activity"


class ProcessEdge(BaseModel):
    source: str
    target: str
    label: str | None = None


class ProcessMap(BaseModel):
    nodes: list[ProcessNode] = Field(default_factory=list)
    edges: list[ProcessEdge] = Field(default_factory=list)
    actors: list[str] = Field(default_factory=list)
    systems: list[str] = Field(default_factory=list)
    exceptions: list[str] = Field(default_factory=list)
    unresolved_steps: list[str] = Field(default_factory=list)
    export_formats: list[str] = Field(default_factory=lambda: ["canonical"])


class ResearchClaim(BaseModel):
    claim_id: str
    text: str
    source_id: str | None = None
    quoted_evidence: str | None = None
    confidence: Confidence = Confidence.LOW
    support_status: str = "insufficient_evidence"


class ResearchSummary(BaseModel):
    claims: list[ResearchClaim] = Field(default_factory=list)
    sources: list[dict[str, Any]] = Field(default_factory=list)
    unresolved_claims: list[str] = Field(default_factory=list)


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str
    session_id: UUID
    title: str
    text: str = Field(min_length=1, max_length=200_000)
    metadata: dict[str, str] = Field(default_factory=dict)


class SourceCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    text: str = Field(min_length=1, max_length=200_000)
    metadata: dict[str, str] = Field(default_factory=dict)


class RetrievalHit(BaseModel):
    source_id: str
    title: str
    excerpt: str
    score: float
    lexical_score: float
    semantic_score: float


class RetrievalResult(BaseModel):
    query: str
    hits: list[RetrievalHit] = Field(default_factory=list)
    attempts: int = 1
    corrected_query: str | None = None


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=10_000)
    min_support_score: float = Field(default=0.2, ge=0, le=1)


class AIOpportunity(BaseModel):
    id: str
    title: str
    process_step: str
    rationale: str
    rank: int
    feasibility: Confidence
    value_evidence: str | None = None
    risks: list[str] = Field(default_factory=list)
    controls: list[str] = Field(default_factory=list)
    human_oversight: str
    confidence: Confidence


class Session(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    vertical: Vertical
    status: SessionStatus = SessionStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    retention_class: str = "default_30_days"
    prompt_versions: dict[str, str] = Field(default_factory=dict)
    model_versions: dict[str, str] = Field(default_factory=dict)


class SessionCreate(BaseModel):
    vertical: Vertical
    process_description: str = Field(min_length=1, max_length=100_000)


class RequirementsRequest(BaseModel):
    process_description: str = Field(min_length=1, max_length=100_000)
    discovery_answers: dict[str, str | None] = Field(default_factory=dict)


class RunEvent(BaseModel):
    session_id: UUID
    node: str
    status: str
    message: str
    retry_count: int = 0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GraphState(BaseModel):
    session: Session
    process_description: str
    redacted_description: str | None = None
    discovery_answers: dict[str, str | None] = Field(default_factory=dict)
    requirements: RequirementsDoc | None = None
    process_map: ProcessMap | None = None
    research: ResearchSummary | None = None
    opportunities: list[AIOpportunity] = Field(default_factory=list)
    events: list[RunEvent] = Field(default_factory=list)
    review_required: bool = False
