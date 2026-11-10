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
    redacted = text
    count = 0
    entity_types: list[str] = []
    for entity_type, pattern in _PATTERNS:
        redacted, replacements = pattern.subn(f"[REDACTED_{entity_type}]", redacted)
        if replacements:
            count += replacements
            entity_types.append(entity_type)
    return RedactionResult(redacted, count, tuple(entity_types))
