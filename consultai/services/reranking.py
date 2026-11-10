import os

from ..models import RetrievalHit


class RerankerError(RuntimeError):
    """Raised when an enabled cross-encoder cannot rerank candidates."""


def rerank(query: str, hits: list[RetrievalHit]) -> list[RetrievalHit]:
    if os.getenv("CONSULTAI_RERANKER_ENABLED", "false").lower() != "true" or len(hits) < 2:
        return hits
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as exc:
        raise RerankerError(
            "Cross-encoder reranking is enabled but sentence-transformers is not installed"
        ) from exc
    model_name = os.getenv(
        "CONSULTAI_RERANKER_MODEL",
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
    )
    try:
        model = CrossEncoder(model_name)
        scores = model.predict([(query, hit.excerpt) for hit in hits])
    except Exception as exc:
        raise RerankerError("Cross-encoder reranking failed") from exc
    reranked = [
        hit.model_copy(update={"score": round(float(score), 4)})
        for hit, score in zip(hits, scores, strict=True)
    ]
    return sorted(reranked, key=lambda hit: hit.score, reverse=True)
