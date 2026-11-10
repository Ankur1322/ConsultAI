import os
import re
from collections import Counter
from uuid import UUID, uuid4

from ..models import RetrievalHit, RetrievalResult, SourceCreate, SourceDocument
from .persistence import Repository
from .observability import increment
from .embeddings import EmbeddingError, embed_text
from .reranking import rerank

_TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.lower())


class EvidenceStore:
    """Session-scoped evidence store with deterministic hybrid retrieval."""

    def __init__(self, repository: Repository | None = None) -> None:
        self._documents: dict[UUID, dict[str, SourceDocument]] = {}
        self.repository = repository

    def add(self, session_id: UUID, payload: SourceCreate) -> SourceDocument:
        document = SourceDocument(
            source_id=f"src-{uuid4().hex[:12]}",
            session_id=session_id,
            title=payload.title,
            text=payload.text,
            metadata=payload.metadata,
        )
        embedding = None
        if os.getenv("CONSULTAI_EMBEDDINGS_ENABLED", "false").lower() == "true":
            try:
                embedding = embed_text(f"{document.title}\n{document.text}")
                if embedding is not None and len(embedding) != 768:
                    embedding = None
            except EmbeddingError:
                embedding = None
        if self.repository is not None:
            self.repository.add_source(session_id, document, embedding=embedding)
        else:
            self._documents.setdefault(session_id, {})[document.source_id] = document
        return document

    def list(self, session_id: UUID) -> list[SourceDocument]:
        if self.repository is not None:
            return self.repository.list_sources(session_id)
        return list(self._documents.get(session_id, {}).values())

    def retrieve(self, session_id: UUID, query: str, top_k: int = 5) -> RetrievalResult:
        increment("retrieval_calls_total")
        query_tokens = Counter(_tokens(query))
        query_embedding = None
        if os.getenv("CONSULTAI_EMBEDDINGS_ENABLED", "false").lower() == "true":
            try:
                query_embedding = embed_text(query)
            except EmbeddingError:
                query_embedding = None
        if self.repository is not None:
            documents = self.repository.search_sources(session_id, query, query_embedding=query_embedding)
            if not documents:
                documents = self.list(session_id)
        else:
            documents = self.list(session_id)
        scored: list[RetrievalHit] = []
        for document in documents:
            document_tokens = Counter(_tokens(document.text))
            shared = sum((query_tokens & document_tokens).values())
            lexical = shared / max(sum(query_tokens.values()), 1)
            semantic = self._semantic_overlap(query_tokens, document_tokens)
            score = (0.6 * lexical) + (0.4 * semantic)
            if score <= 0:
                continue
            scored.append(
                RetrievalHit(
                    source_id=document.source_id,
                    title=document.title,
                    excerpt=document.text[:500],
                    score=round(score, 4),
                    lexical_score=round(lexical, 4),
                    semantic_score=round(semantic, 4),
                )
            )
        scored.sort(key=lambda hit: hit.score, reverse=True)
        reranked = rerank(query, scored[:top_k])
        return RetrievalResult(query=query, hits=reranked[:top_k])

    @staticmethod
    def _semantic_overlap(query_tokens: Counter[str], document_tokens: Counter[str]) -> float:
        query_terms = set(query_tokens)
        document_terms = set(document_tokens)
        if not query_terms:
            return 0.0
        return len(query_terms & document_terms) / len(query_terms)

    def corrective_retrieve(
        self,
        session_id: UUID,
        query: str,
        top_k: int = 5,
        min_score: float = 0.2,
        max_attempts: int = 2,
    ) -> RetrievalResult:
        result = self.retrieve(session_id, query, top_k)
        attempts = 1
        corrected_query: str | None = None
        while attempts < max_attempts and (not result.hits or result.hits[0].score < min_score):
            attempts += 1
            corrected_query = self._correct_query(query)
            result = self.retrieve(session_id, corrected_query, top_k)
            if result.hits and result.hits[0].score >= min_score:
                break
        result.attempts = attempts
        result.corrected_query = corrected_query
        return result

    @staticmethod
    def _correct_query(query: str) -> str:
        tokens = _tokens(query)
        return " ".join(token for token in tokens if len(token) > 2)


evidence_store = EvidenceStore()
