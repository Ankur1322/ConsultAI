from typing import Any


def assess_opportunity_risk(opportunity: dict[str, Any]) -> dict[str, Any]:
    risks = list(opportunity.get("risks", []))
    controls = list(opportunity.get("controls", []))
    if not risks:
        risks.append("Operational and data risks have not been fully assessed.")
    if not controls:
        controls.append("Require human approval before production action.")
    severity = "high" if len(risks) >= 2 else "medium"
    return {
        "opportunity_id": opportunity.get("id", "unknown"),
        "severity": severity,
        "risks": risks,
        "controls": controls,
        "human_oversight_required": True,
    }
