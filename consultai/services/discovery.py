import re

from ..models import DiscoveryQuestion, DiscoveryResult, Vertical

TOPICS = (
    ("actors", "Which people, teams, or roles perform or approve each step?"),
    ("systems", "Which systems, inboxes, or tools are used at each step?"),
    ("exceptions", "What exceptions, escalations, or failure paths occur?"),
    ("controls", "What security, compliance, or approval controls apply?"),
    ("measures", "What volume, error-rate, cost, or response-time measures are available?"),
)


def _has_topic(text: str, topic: str) -> bool:
    patterns = {
        "actors": r"\b(agents?|teams?|roles?|manager|customer|vendor|employee|approver)\b",
        "systems": r"\b(system|email|inbox|erp|crm|portal|spreadsheet|tool)\b",
        "exceptions": r"\b(exception|escalat|fail|error|reject|missing|dispute)\b",
        "controls": r"\b(approve|approval|control|security|compliance|audit|permission)\b",
        "measures": r"\b(volume|rate|cost|time|sla|per day|per month|percent|percentage)\b",
    }
    return re.search(patterns[topic], text, flags=re.IGNORECASE) is not None


def generate_discovery(process_description: str, vertical: Vertical) -> DiscoveryResult:
    missing = [topic for topic, _ in TOPICS if not _has_topic(process_description, topic)]
    questions = [
        DiscoveryQuestion(id=f"DQ-{index:03d}", text=dict(TOPICS)[topic], rationale=f"Missing {topic} context.")
        for index, topic in enumerate(missing, start=1)
    ]
    if not questions:
        return DiscoveryResult(missing_topics=[])
    return DiscoveryResult(questions=questions, missing_topics=missing)
