from pathlib import Path


class PromptLoadError(RuntimeError):
    """Raised when a required versioned prompt cannot be loaded."""


def load_prompt(prompt_name: str, version: str) -> str:
    root = Path(__file__).resolve().parents[2]
    path = root / "prompts" / prompt_name / f"{version}.md"
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PromptLoadError(f"Unable to load prompt {prompt_name}/{version}") from exc
