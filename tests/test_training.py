import json
from pathlib import Path

from consultai.training.baseline import compare
from consultai.training.dataset_builder import build_records


def test_dataset_builder_normalizes_examples(tmp_path: Path) -> None:
    source = Path("data/training/examples.jsonl")
    output = tmp_path / "normalized.jsonl"
    count = build_records(source, output)
    assert count == 2
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["input"]["process_description"]
    assert rows[0]["output"]["functional"]


def test_baseline_comparison_scores_valid_prediction(tmp_path: Path) -> None:
    expected = tmp_path / "expected.jsonl"
    predicted = tmp_path / "predicted.jsonl"
    record = {
        "output": {
            "functional": [
                {
                    "id": "FR-001",
                    "text": "The system shall process invoices.",
                    "acceptance_criterion": "Given an invoice, processing is recorded.",
                }
            ]
        }
    }
    line = json.dumps(record) + "\n"
    expected.write_text(line, encoding="utf-8")
    predicted.write_text(line, encoding="utf-8")
    result = compare(expected, predicted)
    assert result["aggregate"]["composite"] == 1.0
