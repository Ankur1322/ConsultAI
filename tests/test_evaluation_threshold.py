from consultai.services.evaluator import evaluate_requirements


def test_quality_regression_threshold() -> None:
    document = {
        "goals": [], "functional": [{
            "id": "FR-001",
            "text": "The system shall validate invoices.",
            "source_type": "stated",
            "confidence": "medium",
            "acceptance_criterion": "A reviewer can verify validation.",
        }],
        "non_functional": [], "assumptions": [], "constraints": [], "open_questions": [],
    }
    result = evaluate_requirements(document)
    assert result["passed"]
    assert result["overall"] >= 0.75
