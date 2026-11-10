from uuid import uuid4

from consultai.models import SourceCreate
from consultai.services.retrieval import EvidenceStore


def test_memory_retrieval_keeps_session_boundary() -> None:
    store = EvidenceStore()
    session_id = uuid4()
    other = uuid4()
    store.add(session_id, SourceCreate(title="Allowed", text="Payment approval policy."))
    store.add(other, SourceCreate(title="Other", text="Payment approval policy."))
    result = store.retrieve(session_id, "payment approval")
    assert [hit.title for hit in result.hits] == ["Allowed"]
