import os
from contextlib import AbstractContextManager
from typing import Any


class LangGraphCheckpointError(RuntimeError):
    """Raised when the optional LangGraph PostgreSQL checkpointer is unavailable."""


def postgres_checkpointer() -> AbstractContextManager[Any]:
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
    except ImportError as exc:
        raise LangGraphCheckpointError(
            "Install the graph dependency extra to enable LangGraph PostgreSQL checkpoints"
        ) from exc
    database_url = os.getenv("CONSULTAI_DATABASE_URL")
    if not database_url:
        raise LangGraphCheckpointError("CONSULTAI_DATABASE_URL is required for LangGraph checkpoints")
    return PostgresSaver.from_conn_string(database_url)


def checkpoint_config(thread_id: str) -> dict[str, dict[str, str]]:
    return {"configurable": {"thread_id": thread_id}}
