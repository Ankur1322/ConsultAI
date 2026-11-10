# Persistent Storage Implementation

Docker mode sets `CONSULTAI_STORAGE=postgres`. The API creates these tables on
startup/use:

- `consultai_sessions`: current typed graph state and session lifecycle.
- `consultai_sources`: redacted source documents scoped by session.
- `consultai_checkpoints`: append-only state snapshots used for resume and audit.

The repository is deliberately explicit: PostgreSQL connection failures raise a
`PersistenceError`; production mode does not silently fall back to memory.
Memory mode is retained only for offline tests and local development without
the database service.

The next storage hardening step is replacing the custom checkpoint table with
the official LangGraph PostgreSQL checkpointer once the graph is migrated to a
compiled `StateGraph`.
