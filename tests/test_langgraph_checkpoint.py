import pytest
import sys

from consultai.services.langgraph_checkpoint import checkpoint_config, postgres_checkpointer


def test_checkpoint_config_uses_session_thread() -> None:
    assert checkpoint_config("session-123") == {
        "configurable": {"thread_id": "session-123"},
    }


def test_checkpointer_requires_optional_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "langgraph", None)
    monkeypatch.delenv("CONSULTAI_DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="Install the graph dependency"):
        postgres_checkpointer()
