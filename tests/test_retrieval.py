from uuid import uuid4

from consultai.models import SourceCreate
from consultai.services.citations import build_research_summary
from consultai.services.retrieval import EvidenceStore


def test_session_scoped_hybrid_retrieval() -> None:
    store = EvidenceStore()
    session_id = uuid4()
    other_session = uuid4()
    store.add(session_id, SourceCreate(title="Invoice policy", text="Invoices require manager approval before payment."))
    store.add(other_session, SourceCreate(title="Support policy", text="Support tickets require customer verification."))
    result = store.retrieve(session_id, "manager approval payment")
    assert result.hits
    assert result.hits[0].title == "Invoice policy"
    assert not store.retrieve(session_id, "customer verification").hits


def test_corrective_retrieval_records_retry() -> None:
    store = EvidenceStore()
    session_id = uuid4()
    store.add(session_id, SourceCreate(title="Support policy", text="Support tickets require customer verification."))
    result = store.corrective_retrieve(session_id, "support verification workflow", min_score=0.8)
    assert result.attempts == 2
    assert result.corrected_query


def test_citation_verifier_rejects_unsupported_claim() -> None:
    store = EvidenceStore()
    session_id = uuid4()
    store.add(session_id, SourceCreate(title="Policy", text="Invoices require manager approval."))
    hits = store.retrieve(session_id, "What is the employee vacation allowance?").hits
    summary = build_research_summary("Employees receive thirty days of vacation.", hits)
    assert summary.claims[0].text == "insufficient evidence"
    assert summary.claims[0].source_id is None
