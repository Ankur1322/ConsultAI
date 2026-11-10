# ConsultAI Limitations

## Current implementation

- Session state and evidence are held in memory; restarting the API loses active sessions and uploaded sources.
- The retrieval implementation is a deterministic offline baseline. It does not yet use PostgreSQL pgvector, a production BM25 index, or a cross-encoder service.
- The QLoRA notebook is a configuration scaffold. No training run or quality improvement is claimed.
- The evaluator is rubric-based and deterministic. It is not a substitute for human review or a validated LLM-as-judge.
- PII redaction currently covers common email, phone, and credit-card patterns. Presidio integration is still required for broader entity coverage.
- API-key authentication is a deployment guard, not a complete identity, tenant isolation, or authorization system.
- Docker Compose starts PostgreSQL and Ollama, but the current API does not persist to PostgreSQL or automatically download an Ollama model.

## Operational requirements before production

1. Replace in-memory stores with PostgreSQL repositories and LangGraph checkpointing.
2. Configure a secret manager and rotate API keys.
3. Add tenant-aware authorization and audit retention controls.
4. Run red-team tests for prompt injection, poisoned sources, PII variants, and citation manipulation.
5. Establish a frozen evaluation set and measure latency, cost, retrieval quality, citation support, and human-review rates.
