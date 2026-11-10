from uuid import uuid4

import pytest

from consultai.models import GraphState, Session, SourceCreate, Vertical
from consultai.services.persistence import Repository


def test_repository_requires_postgres_when_connecting(monkeypatch: pytest.MonkeyPatch) -> None:
    repository = Repository()
    monkeypatch.setattr(repository, "database_url", "postgresql://invalid:invalid@127.0.0.1:1/invalid")
    with pytest.raises(RuntimeError, match="Unable to connect"):
        repository.get_session(uuid4())


def test_graph_state_payload_is_json_serializable() -> None:
    state = GraphState(session=Session(vertical=Vertical.INVOICE_TO_PAY), process_description="Invoice approval.")
    assert state.model_dump(mode="json")["session"]["vertical"] == "invoice_to_pay"
