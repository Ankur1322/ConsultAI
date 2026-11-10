from typing import Any


RUBRIC_WEIGHTS = {
    "schema_valid": 0.25,
    "testability": 0.25,
    "evidence_grounding": 0.25,
    "completeness": 0.25,
}


def evaluate_requirements(document: dict[str, Any]) -> dict[str, Any]:
    functional = document.get("functional", [])
    schema_valid = all(
        isinstance(item, dict)
        and bool(item.get("id"))
        and bool(item.get("text"))
        and bool(item.get("confidence"))
        for item in functional
    )
    testable = all(
        isinstance(item.get("text"), str)
        and item["text"].startswith("The system shall")
        and bool(item.get("acceptance_criterion"))
        for item in functional
    )
    grounded = all(item.get("source_type") in {"stated", "inferred"} for item in functional)
    completeness = all(key in document for key in ("goals", "functional", "non_functional", "assumptions", "constraints", "open_questions"))
    scores = {
        "schema_valid": float(schema_valid),
        "testability": float(testable),
        "evidence_grounding": float(grounded),
        "completeness": float(completeness),
    }
    overall = sum(scores[key] * RUBRIC_WEIGHTS[key] for key in scores)
    return {"scores": scores, "overall": round(overall, 4), "passed": overall >= 0.75}
