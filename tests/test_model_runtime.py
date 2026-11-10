import json

import pytest

from consultai.services.model_runtime import ModelRuntimeError, generate_json


def test_model_runtime_is_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CONSULTAI_LLM_ENABLED", raising=False)
    assert generate_json("ignored") is None


def test_enabled_runtime_rejects_unsupported_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONSULTAI_LLM_ENABLED", "true")
    monkeypatch.setenv("CONSULTAI_MODEL_PROVIDER", "unknown")
    with pytest.raises(ModelRuntimeError, match="Unsupported"):
        generate_json("ignored")
