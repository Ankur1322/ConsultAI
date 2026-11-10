# ConsultAI Phase 1 Decision Log

## D-001: Modular LangGraph supervisor

- Decision: Use a modular LangGraph supervisor with typed node contracts.
- Alternatives: A linear workflow-first pipeline; an event-driven job architecture.
- Reason: The supervisor directly supports checkpointing, critic routing, bounded retries, and human-review interrupts while remaining manageable for a local-Docker pilot.

## D-002: Local-first runtime

- Decision: Design the first deployment for local Docker with Ollama as the default model provider.
- Alternatives: Azure-first deployment; cloud-agnostic production deployment.
- Reason: Local-first reduces privacy exposure and operational scope while the product and evaluation contracts are established.

## D-003: Application-enforced safety boundaries

- Decision: Enforce PII redaction, retrieval authorization, and provider policy in application services.
- Alternative: Rely primarily on system prompts and model behavior.
- Reason: Prompt instructions are not an execution or authorization boundary, especially when uploaded and retrieved text is untrusted.

## D-004: Evidence-first research output

- Decision: Require source metadata and support status on every factual research claim.
- Alternative: Allow a prose summary with citations only at paragraph level.
- Reason: Claim-level verification makes unsupported evidence visible and permits a deterministic "insufficient evidence" outcome.

## D-005: Authentication deferred

- Decision: Keep phase 1 single-user/local while preserving session and tenant boundaries in contracts.
- Alternative: Implement multi-user identity and tenant administration from phase 1.
- Reason: This keeps the initial architecture focused without preventing secure multi-user work in phase 7.
