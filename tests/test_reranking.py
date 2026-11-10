import pytest
import sys

from consultai.models import RetrievalHit
from consultai.services.reranking import RerankerError, rerank


def test_reranking_is_disabled_by_default() -> None:
    hits = [
        RetrievalHit(source_id="a", title="A", excerpt="one", score=0.8, lexical_score=0.8, semantic_score=0.8),
        RetrievalHit(source_id="b", title="B", excerpt="two", score=0.5, lexical_score=0.5, semantic_score=0.5),
    ]
    assert rerank("query", hits) == hits


def test_enabled_reranking_requires_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONSULTAI_RERANKER_ENABLED", "true")
    monkeypatch.setitem(sys.modules, "sentence_transformers", None)
    with pytest.raises(RerankerError, match="sentence-transformers"):
        rerank("query", [
            RetrievalHit(source_id="a", title="A", excerpt="one", score=0.8, lexical_score=0.8, semantic_score=0.8),
            RetrievalHit(source_id="b", title="B", excerpt="two", score=0.5, lexical_score=0.5, semantic_score=0.5),
        ])
