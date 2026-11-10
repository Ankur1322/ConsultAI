from collections.abc import Callable
from typing import Any

from .models import (
    AIOpportunity,
    GraphState,
    ProcessMap,
    ResearchSummary,
    RequirementItem,
    RequirementsDoc,
    RunEvent,
    SessionStatus,
)
from .services.discovery import generate_discovery
from .services.critic import critic_decision
from .services.evaluator import evaluate_requirements
from .services.requirements_agent import build_requirements
from .services.risk import assess_opportunity_risk

Node = Callable[[GraphState], GraphState]

NODE_NAMES = (
    "intake_redaction",
    "discovery",
    "requirements",
    "process_map",
    "research",
    "evaluator",
    "risk_check",
    "critic",
    "human_review",
    "composer",
)


def _event(state: GraphState, node: str, message: str) -> GraphState:
    state.events.append(RunEvent(session_id=state.session.id, node=node, status="completed", message=message))
    return state


def intake_redaction(state: GraphState) -> GraphState:
    # Phase 2 stub: Presidio integration is intentionally deferred.
    state.redacted_description = state.process_description
    return _event(state, "intake_redaction", "Input accepted as untrusted data; redaction adapter pending.")


def discovery(state: GraphState) -> GraphState:
    result = generate_discovery(state.redacted_description or state.process_description, state.session.vertical)
    state.discovery_answers = {question.id: None for question in result.questions}
    return _event(state, "discovery", f"Generated {len(result.questions)} discovery questions.")


def requirements(state: GraphState) -> GraphState:
    state.requirements = build_requirements(
        state.redacted_description or state.process_description,
        state.discovery_answers,
    )
    return _event(state, "requirements", "Requirements agent produced a validated document.")


def process_map(state: GraphState) -> GraphState:
    state.process_map = ProcessMap(unresolved_steps=["Process mapping agent is not implemented yet."])
    return _event(state, "process_map", "Process map stub produced a validated document.")


def research(state: GraphState) -> GraphState:
    state.research = ResearchSummary(unresolved_claims=["Research connectors are not configured in phase 2."])
    return _event(state, "research", "Research stub produced an evidence-safe document.")


def evaluator(state: GraphState) -> GraphState:
    if state.requirements is None:
        state.evaluation = {"passed": False, "overall": 0.0, "scores": {}}
    else:
        state.evaluation = evaluate_requirements(state.requirements.model_dump(mode="json"))
    return _event(state, "evaluator", "Requirements evaluated against the phase 6 rubric.")


def risk_check(state: GraphState) -> GraphState:
    state.opportunities = [
        AIOpportunity(
            id="AI-001",
            title="Opportunity analysis pending",
            process_step="unresolved",
            rationale="The risk and opportunity agents are deferred to phase 6.",
            rank=1,
            feasibility="low",
            human_oversight="Required",
            confidence="low",
        )
    ]
    state.risk_assessments = [
        assess_opportunity_risk(opportunity.model_dump(mode="json"))
        for opportunity in state.opportunities
    ]
    return _event(state, "risk_check", "AI opportunities received risk assessments and controls.")


def critic(state: GraphState) -> GraphState:
    state.critic_result = critic_decision(state.evaluation or {"passed": False})
    if not state.critic_result["passed"]:
        state.review_required = True
        state.session.status = SessionStatus.REVIEW
    return _event(state, "critic", "Critic checked rubric status and bounded retry routing.")


def human_review(state: GraphState) -> GraphState:
    return _event(state, "human_review", "Human review interrupt adapter is deferred.")


def composer(state: GraphState) -> GraphState:
    state.session.status = SessionStatus.COMPLETED
    return _event(state, "composer", "Composer stub completed the phase 2 package.")


NODE_HANDLERS: dict[str, Node] = {
    name: handler
    for name, handler in (
        ("intake_redaction", intake_redaction),
        ("discovery", discovery),
        ("requirements", requirements),
        ("process_map", process_map),
        ("research", research),
        ("evaluator", evaluator),
        ("risk_check", risk_check),
        ("critic", critic),
        ("human_review", human_review),
        ("composer", composer),
    )
}


def run_graph(state: GraphState) -> GraphState:
    for name in NODE_NAMES:
        state = NODE_HANDLERS[name](state)
    return state


run_stub_graph = run_graph
