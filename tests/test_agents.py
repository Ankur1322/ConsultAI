from consultai.models import SourceType, Vertical
from consultai.services.discovery import generate_discovery
from consultai.services import requirements_agent
from consultai.services.requirements_agent import build_requirements


def test_discovery_identifies_missing_operational_topics() -> None:
    result = generate_discovery("Agents copy invoices from email.", Vertical.INVOICE_TO_PAY)
    assert "actors" not in result.missing_topics
    assert "systems" not in result.missing_topics
    assert "measures" in result.missing_topics
    assert result.questions


def test_requirements_are_structured_and_low_confidence_without_metrics() -> None:
    result = build_requirements("Agents answer password-reset questions.", {})
    assert result.functional[0].text.startswith("The system shall")
    assert result.functional[0].acceptance_criterion
    assert result.functional[0].source_type == SourceType.STATED
    assert result.open_questions[0].confidence == "low"


def test_requirements_redacts_pii_before_rendering_a_model_prompt(monkeypatch) -> None:
    captured: dict[str, str] = {}

    def capture_prompt(prompt: str) -> None:
        captured["prompt"] = prompt
        return None

    monkeypatch.setattr(requirements_agent, "generate_json", capture_prompt)

    build_requirements(
        "Contact alice@example.com about invoice approval.",
        {"DQ-001": "Call +1 555-123-4567 if approval is delayed."},
    )

    assert "alice@example.com" not in captured["prompt"]
    assert "555-123-4567" not in captured["prompt"]
    assert "EMAIL_ADDRESS" in captured["prompt"]
    assert "PHONE_NUMBER" in captured["prompt"]
