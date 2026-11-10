import re

from ..models import (
    Confidence,
    DiscoveryResult,
    RequirementItem,
    RequirementsDoc,
    SourceType,
)
from .prompt_loader import load_prompt
from .model_runtime import generate_json


def _sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text.strip()) if sentence.strip()]


def build_requirements(process_description: str, answers: dict[str, str | None]) -> RequirementsDoc:
    prompt = load_prompt("requirements_agent", "v1")
    if "Return JSON matching the `RequirementsDoc` schema" not in prompt:
        raise RuntimeError("Requirements prompt contract is invalid")
    rendered = prompt.replace("{{description}}", process_description).replace("{{discovery_answers}}", str(answers))
    model_result = generate_json(rendered)
    if model_result is not None:
        try:
            return RequirementsDoc.model_validate(model_result)
        except Exception as exc:
            raise RuntimeError("Model output failed RequirementsDoc validation") from exc

    sentences = _sentences(process_description)
    functional = [
        RequirementItem(
            id=f"FR-{index:03d}",
            text=f"The system shall support the process activity described as: {sentence}",
            source_type=SourceType.STATED,
            evidence=sentence,
            confidence=Confidence.MEDIUM,
            acceptance_criterion=f"Given the stated activity, a reviewer can verify that the activity is represented in the generated output.",
        )
        for index, sentence in enumerate(sentences, start=1)
    ]
    missing_metrics = not any(
        re.search(r"\b(volume|rate|cost|time|sla|percent|percentage)\b", value or "", re.IGNORECASE)
        for value in [process_description, *answers.values()]
    )
    open_questions = [
        RequirementItem(
            id="Q-001",
            text="What volume, error-rate, cost, and response-time data is available?",
            source_type=SourceType.INFERRED,
            confidence=Confidence.LOW,
        )
    ] if missing_metrics else []
    return RequirementsDoc(
        goals=[
            RequirementItem(
                id="G-001",
                text="Improve the described business process.",
                source_type=SourceType.INFERRED,
                evidence=sentences[0] if sentences else None,
                confidence=Confidence.MEDIUM,
            )
        ],
        functional=functional,
        non_functional=[],
        assumptions=[],
        constraints=[],
        open_questions=open_questions,
    )
