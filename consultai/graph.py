from collections.abc import Callable
from typing import Any, TypedDict

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from .models import AIOpportunity, GraphState, ProcessMap, ResearchSummary, ReviewDecision, RunEvent, SessionStatus
from .services.critic import critic_decision
from .services.discovery import generate_discovery
from .services.evaluator import evaluate_requirements
from .services.requirements_agent import build_requirements
from .services.risk import assess_opportunity_risk

Node = Callable[[GraphState], GraphState]

NODE_NAMES = (
    "intake_redaction", "discovery", "requirements", "process_map", "research",
    "evaluator", "risk_check", "critic", "human_review", "composer",
)


class GraphEnvelope(TypedDict):
    """LangGraph's JSON-serializable envelope around the Pydantic state contract."""

    state: dict[str, Any]


def _event(state: GraphState, node: str, message: str) -> GraphState:
    state.events.append(RunEvent(session_id=state.session.id, node=node, status="completed", message=message))
    return state


def intake_redaction(state: GraphState) -> GraphState:
    # The API boundary redacts user input before the graph starts.
    state.redacted_description = state.redacted_description or state.process_description
    return _event(state, "intake_redaction", "Input accepted as untrusted data and passed through the redaction boundary.")


def discovery(state: GraphState) -> GraphState:
    result = generate_discovery(state.redacted_description or state.process_description, state.session.vertical)
    state.discovery_answers = {question.id: None for question in result.questions}
    return _event(state, "discovery", f"Generated {len(result.questions)} discovery questions.")


def requirements(state: GraphState) -> GraphState:
    state.requirements = build_requirements(state.redacted_description or state.process_description, state.discovery_answers)
    return _event(state, "requirements", "Requirements agent produced a validated document.")


def process_map(state: GraphState) -> GraphState:
    state.process_map = ProcessMap(unresolved_steps=["Process mapping agent is not implemented yet."])
    return _event(state, "process_map", "Process map stub produced a validated document.")


def research(state: GraphState) -> GraphState:
    state.research = ResearchSummary(unresolved_claims=["Research connectors are not configured in the graph yet."])
    return _event(state, "research", "Research stub produced an evidence-safe document.")


def evaluator(state: GraphState) -> GraphState:
    state.evaluation = (
        evaluate_requirements(state.requirements.model_dump(mode="json"))
        if state.requirements else {"passed": False, "overall": 0.0, "scores": {}}
    )
    return _event(state, "evaluator", "Requirements evaluated against the phase 6 rubric.")


def risk_check(state: GraphState) -> GraphState:
    state.opportunities = [AIOpportunity(
        id="AI-001", title="Opportunity analysis pending", process_step="unresolved",
        rationale="The risk and opportunity agents are deferred to phase 6.", rank=1,
        feasibility="low", human_oversight="Required", confidence="low",
    )]
    state.risk_assessments = [assess_opportunity_risk(item.model_dump(mode="json")) for item in state.opportunities]
    return _event(state, "risk_check", "AI opportunities received risk assessments and controls.")


def critic(state: GraphState) -> GraphState:
    state.critic_result = critic_decision(state.evaluation or {"passed": False})
    if not state.critic_result["passed"]:
        state.review_required = True
        state.session.status = SessionStatus.REVIEW
    return _event(state, "critic", "Critic checked rubric status and bounded retry routing.")


def human_review(state: GraphState) -> GraphState:
    """Record the no-review path; review-required runs pause in the LangGraph node."""
    if state.review_required:
        state.session.status = SessionStatus.REVIEW
        return state
    return _event(state, "human_review", "Human review was not required.")


def composer(state: GraphState) -> GraphState:
    state.session.status = SessionStatus.COMPLETED
    return _event(state, "composer", "Composer stub completed the package.")


NODE_HANDLERS: dict[str, Node] = dict(zip(NODE_NAMES, (
    intake_redaction, discovery, requirements, process_map, research,
    evaluator, risk_check, critic, human_review, composer,
)))


def _pack(state: GraphState) -> GraphEnvelope:
    return {"state": state.model_dump(mode="json")}


def _unpack(envelope: GraphEnvelope) -> GraphState:
    return GraphState.model_validate(envelope["state"])


def _node_adapter(name: str) -> Callable[[GraphEnvelope], GraphEnvelope]:
    def invoke(envelope: GraphEnvelope) -> GraphEnvelope:
        return _pack(NODE_HANDLERS[name](_unpack(envelope)))
    return invoke


def _human_review_node(envelope: GraphEnvelope) -> GraphEnvelope:
    state = _unpack(envelope)
    if not state.review_required:
        return _pack(human_review(state))
    decision = interrupt(
        {
            "session_id": str(state.session.id),
            "reason": (state.critic_result or {}).get("failures", ["Human review required"]),
            "allowed_actions": ["approve", "reject"],
        },
        response_schema=ReviewDecision,
    )
    validated = decision if isinstance(decision, ReviewDecision) else ReviewDecision.model_validate(decision)
    state.events.append(RunEvent(
        session_id=state.session.id, node="human_review",
        status="approved" if validated.approved else "rejected",
        message=validated.comment or ("Human review approved." if validated.approved else "Human review rejected."),
    ))
    if not validated.approved:
        state.session.status = SessionStatus.FAILED
        return _pack(state)
    state.review_required = False
    state.session.status = SessionStatus.RUNNING
    return _pack(state)


def _after_human_review(envelope: GraphEnvelope) -> str:
    return END if _unpack(envelope).session.status == SessionStatus.FAILED else "composer"


def build_graph(checkpointer: BaseCheckpointSaver | None = None):
    """Compile the supervisor with a caller-supplied durable checkpointer."""
    builder = StateGraph(GraphEnvelope)
    for name in NODE_NAMES:
        builder.add_node(name, _human_review_node if name == "human_review" else _node_adapter(name))
    builder.add_edge(START, "intake_redaction")
    for current, following in zip(NODE_NAMES, NODE_NAMES[1:]):
        if current != "human_review":
            builder.add_edge(current, following)
    builder.add_conditional_edges("human_review", _after_human_review, {"composer": "composer", END: END})
    builder.add_edge("composer", END)
    return builder.compile(checkpointer=checkpointer or InMemorySaver())


_DEFAULT_GRAPH = build_graph()


def _config(state: GraphState) -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": str(state.session.id)}}


def run_graph(state: GraphState, graph: Any | None = None) -> GraphState:
    return _unpack((graph or _DEFAULT_GRAPH).invoke(_pack(state), _config(state)))


run_stub_graph = run_graph


def resume_graph(state: GraphState, approved: bool, comment: str | None = None, graph: Any | None = None) -> GraphState:
    if state.session.status != SessionStatus.REVIEW:
        raise ValueError("Session is not waiting for human review")
    result = (graph or _DEFAULT_GRAPH).invoke(
        Command(resume=ReviewDecision(approved=approved, comment=comment)), _config(state)
    )
    return _unpack(result)
