from consultai.services.critic import critic_decision
from consultai.services.evaluator import evaluate_requirements
from consultai.services.risk import assess_opportunity_risk


def test_evaluator_passes_valid_requirements() -> None:
    document = {
        "goals": [],
        "functional": [
            {
                "id": "FR-001",
                "text": "The system shall record invoices.",
                "source_type": "stated",
                "confidence": "high",
                "acceptance_criterion": "Given an invoice, it is recorded.",
            }
        ],
        "non_functional": [],
        "assumptions": [],
        "constraints": [],
        "open_questions": [],
    }
    result = evaluate_requirements(document)
    assert result["passed"] is True
    assert result["overall"] == 1.0


def test_critic_routes_failed_evaluation() -> None:
    result = critic_decision({"passed": False}, citation_verified=False)
    assert result["route"] == "responsible_node"
    assert len(result["failures"]) == 2
    assert result["max_retries"] == 2


def test_risk_check_adds_default_controls() -> None:
    result = assess_opportunity_risk({"id": "AI-001", "risks": []})
    assert result["human_oversight_required"] is True
    assert result["controls"]
