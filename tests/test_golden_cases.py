import json
from pathlib import Path

from consultai.models import Vertical
from consultai.services.discovery import generate_discovery
from consultai.services.requirements_agent import build_requirements


def test_all_golden_cases_have_valid_agent_outputs() -> None:
    path = Path("data/evaluation/golden_cases.jsonl")
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(cases) == 20
    for case in cases:
        vertical = Vertical(case["vertical"])
        discovery = generate_discovery(case["process_description"], vertical)
        requirements = build_requirements(case["process_description"], {})
        assert discovery.questions or not case["expected_topics"]
        assert requirements.functional
        assert all(item.text.startswith("The system shall") for item in requirements.functional)
