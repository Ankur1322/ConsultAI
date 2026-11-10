import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ("process_description", "discovery_answers", "requirements")


def validate_case(case: dict[str, Any], line_number: int) -> None:
    missing = [field for field in REQUIRED_FIELDS if field not in case]
    if missing:
        raise ValueError(f"line {line_number}: missing fields: {', '.join(missing)}")
    if not isinstance(case["process_description"], str) or not case["process_description"].strip():
        raise ValueError(f"line {line_number}: process_description must be non-empty text")
    if not isinstance(case["discovery_answers"], dict):
        raise ValueError(f"line {line_number}: discovery_answers must be an object")
    if not isinstance(case["requirements"], dict):
        raise ValueError(f"line {line_number}: requirements must be an object")


def build_records(input_path: Path, output_path: Path) -> int:
    records: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            case = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {line_number}: invalid JSON") from exc
        validate_case(case, line_number)
        records.append(
            {
                "input": {
                    "process_description": case["process_description"],
                    "discovery_answers": case["discovery_answers"],
                },
                "output": case["requirements"],
                "metadata": {
                    "case_id": case.get("case_id", f"case-{len(records) + 1:04d}"),
                    "vertical": case.get("vertical", "unknown"),
                    "source": case.get("source", "curated"),
                },
            }
        )
    if not records:
        raise ValueError("dataset is empty")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    return len(records)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build normalized ConsultAI training JSONL.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(f"wrote {build_records(args.input, args.output)} records")


if __name__ == "__main__":
    main()
