import argparse
import json
from pathlib import Path
from typing import Any


def _functional_items(document: dict[str, Any]) -> list[dict[str, Any]]:
    items = document.get("functional", [])
    return items if isinstance(items, list) else []


def score_prediction(expected: dict[str, Any], predicted: dict[str, Any]) -> dict[str, float]:
    expected_items = _functional_items(expected)
    predicted_items = _functional_items(predicted)
    expected_ids = {item.get("id") for item in expected_items}
    predicted_ids = {item.get("id") for item in predicted_items}
    id_recall = len(expected_ids & predicted_ids) / max(len(expected_ids), 1)
    valid_sentences = sum(
        isinstance(item.get("text"), str) and item["text"].startswith("The system shall")
        for item in predicted_items
    )
    testability = valid_sentences / max(len(predicted_items), 1)
    acceptance = sum(bool(item.get("acceptance_criterion")) for item in predicted_items)
    acceptance_rate = acceptance / max(len(predicted_items), 1)
    return {
        "functional_id_recall": round(id_recall, 4),
        "testable_sentence_rate": round(testability, 4),
        "acceptance_criterion_rate": round(acceptance_rate, 4),
        "composite": round((id_recall + testability + acceptance_rate) / 3, 4),
    }


def compare(expected_path: Path, predicted_path: Path) -> dict[str, Any]:
    expected = [json.loads(line) for line in expected_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    predicted = [json.loads(line) for line in predicted_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(expected) != len(predicted):
        raise ValueError("expected and predicted JSONL files must have the same number of records")
    scores = [score_prediction(item["output"], prediction["output"]) for item, prediction in zip(expected, predicted)]
    aggregate = {
        key: round(sum(score[key] for score in scores) / len(scores), 4)
        for key in scores[0]
    }
    return {"cases": len(scores), "aggregate": aggregate, "per_case": scores}


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare requirements predictions to a normalized dataset.")
    parser.add_argument("expected", type=Path)
    parser.add_argument("predicted", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(args.expected, args.predicted)
    text = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
