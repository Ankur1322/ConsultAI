from collections.abc import Iterable

from ..models import Confidence, ResearchClaim, ResearchSummary, RetrievalHit
from .observability import increment


def _terms(text: str) -> set[str]:
    return {word.lower().strip(".,:;!?()[]") for word in text.split() if len(word) > 2}


def verify_claim(claim_text: str, hits: Iterable[RetrievalHit]) -> ResearchClaim:
    best = max(hits, key=lambda hit: len(_terms(claim_text) & _terms(hit.excerpt)), default=None)
    if best is None:
        increment("citation_unsupported_total")
        return ResearchClaim(claim_id="claim-001", text="insufficient evidence", support_status="insufficient_evidence")
    overlap = len(_terms(claim_text) & _terms(best.excerpt)) / max(len(_terms(claim_text)), 1)
    if overlap < 0.2:
        increment("citation_unsupported_total")
        return ResearchClaim(claim_id="claim-001", text="insufficient evidence", support_status="insufficient_evidence")
    confidence = Confidence.HIGH if overlap >= 0.6 else Confidence.MEDIUM
    increment("citation_supported_total")
    return ResearchClaim(
        claim_id="claim-001",
        text=claim_text,
        source_id=best.source_id,
        quoted_evidence=best.excerpt,
        confidence=confidence,
        support_status="supported",
    )


def build_research_summary(claim_text: str, hits: list[RetrievalHit]) -> ResearchSummary:
    claim = verify_claim(claim_text, hits)
    unresolved = [] if claim.support_status == "supported" else [claim_text]
    sources = [{"source_id": hit.source_id, "title": hit.title} for hit in hits]
    return ResearchSummary(claims=[claim], sources=sources, unresolved_claims=unresolved)
