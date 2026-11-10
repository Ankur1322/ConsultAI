from typing import Any


def critic_decision(evaluation: dict[str, Any], citation_verified: bool = True) -> dict[str, Any]:
    failures: list[str] = []
    if not evaluation.get("passed", False):
        failures.append("requirements rubric did not pass")
    if not citation_verified:
        failures.append("citation support could not be verified")
    return {
        "passed": not failures,
        "failures": failures,
        "route": "composer" if not failures else "responsible_node",
        "max_retries": 2,
    }
