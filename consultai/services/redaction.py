import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RedactionResult:
    text: str
    count: int
    entity_types: tuple[str, ...]


_PATTERNS = (
    ("EMAIL_ADDRESS", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("PHONE_NUMBER", re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)")),
    ("CREDIT_CARD", re.compile(r"(?<!\d)(?:\d[ -]*?){13,19}(?!\d)")),
)


def redact_pii(text: str) -> RedactionResult:
    presidio_result = _redact_with_presidio(text)
    if presidio_result is not None:
        return presidio_result
    return _redact_with_patterns(text)


def _redact_with_presidio(text: str) -> RedactionResult | None:
    try:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine
    except ImportError:
        return None
    try:
        analyzer = AnalyzerEngine()
        results = analyzer.analyze(text=text, language="en")
        if not results:
            return RedactionResult(text, 0, ())
        anonymized = AnonymizerEngine().anonymize(text=text, analyzer_results=results)
        entity_types = tuple(sorted({result.entity_type for result in results}))
        return RedactionResult(anonymized.text, len(results), entity_types)
    except (OSError, RuntimeError, ValueError):
        return None


def _redact_with_patterns(text: str) -> RedactionResult:
    redacted = text
    count = 0
    entity_types: list[str] = []
    for entity_type, pattern in _PATTERNS:
        redacted, replacements = pattern.subn(f"[REDACTED_{entity_type}]", redacted)
        if replacements:
            count += replacements
            entity_types.append(entity_type)
    return RedactionResult(redacted, count, tuple(entity_types))
