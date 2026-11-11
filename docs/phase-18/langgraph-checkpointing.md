# LangGraph checkpointing migration

## Scope

The custom sequential runner has been replaced with a compiled LangGraph
`StateGraph`. The existing Pydantic `GraphState` remains the typed business
contract and is serialized into the graph's state envelope.

## Checkpoint behavior

- Development and unit-test runs use LangGraph `InMemorySaver`.
- When `CONSULTAI_STORAGE=postgres`, the FastAPI lifespan creates a
  `PostgresSaver`, runs its schema setup, and compiles the workflow against it.
- Each session UUID is the LangGraph `thread_id`.
- A review-required run calls LangGraph `interrupt()` with the typed
  `ReviewDecision` schema. The review endpoint resumes using
  `Command(resume=...)`.

## Validation

- A review regression test now starts a graph run, verifies it pauses for
  review, and resumes it through the graph command path.
- Static compilation and diff checks pass in the local workspace.
- Full pytest execution is currently blocked by the host's Python 3.15
  Application Control policy, which prevents `_overlapped` from loading.

## Remaining limits

- The business nodes are still staged implementations; this migration changes
  orchestration and persistence only.
- PostgreSQL/Docker integration must be exercised in a Python 3.11 environment
  with a reachable database before claiming end-to-end runtime validation.
