import json

import pytest

from consultai.services.embeddings import EmbeddingError, embed_text


def test_embeddings_are_disabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CONSULTAI_EMBEDDINGS_ENABLED", raising=False)
    assert embed_text("invoice approval") is None


def test_embeddings_reject_invalid_provider_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONSULTAI_EMBEDDINGS_ENABLED", "true")
    monkeypatch.setenv("CONSULTAI_OLLAMA_BASE_URL", "http://127.0.0.1:1")
    with pytest.raises(EmbeddingError):
        embed_text("invoice approval")
