# LangGraph PostgreSQL checkpointing

The graph deployment extra now includes the official LangGraph PostgreSQL
checkpoint package. The `postgres_checkpointer()` factory uses
`CONSULTAI_DATABASE_URL`, and `checkpoint_config()` binds checkpoints to a
session thread ID.

The current deterministic graph continues using the repository checkpoint
table for compatibility with offline tests. The compiled `StateGraph`
migration is the next graph-runtime step; enabling the extra does not silently
replace the current execution path.
