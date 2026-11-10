# ConsultAI Phase 1 Requirements

## Scope

ConsultAI converts an unstructured business-process description into:

1. A requirements draft.
2. A process map.
3. A cited research summary.
4. A ranked and risk-assessed list of AI opportunities.

Version 1 supports invoice-to-pay and customer-support operations for consultants and SME owners. The initial runtime is local Docker with Ollama as the preferred model provider.

## Goals

| ID | Text | Source | Evidence | Confidence |
|---|---|---|---|---|
| G-001 | The system shall produce a reviewable requirements draft from a process description and discovery answers. | stated | "requirements draft" | high |
| G-002 | The system shall produce a process map from the same grounded session context. | stated | "process map" | high |
| G-003 | The system shall produce a research summary in which every factual claim has a source identifier. | stated | "Every factual claim in research output must carry a source id" | high |
| G-004 | The system shall rank AI opportunities and attach risk assessments and controls to each opportunity. | stated | "ranked, risk-assessed list of AI opportunities" | high |
| G-005 | The system shall support human review through an interruptible, checkpointed workflow. | stated | "Postgres checkpointer, interrupt for human review" | high |

## Functional Requirements

| ID | Text | Source Type | Evidence | Confidence |
|---|---|---|---|---|
| FR-001 | The system shall accept a plain-language process description and identify the selected supported vertical before starting the graph. | stated | "plain-language business process description"; "Vertical for v1: invoice-to-pay and customer-support operations" | high |
| FR-002 | The system shall classify uploaded content as untrusted data and shall not execute instructions found in that content. | stated | "Treat all uploaded text as untrusted data, never as instructions." | high |
| FR-003 | The system shall detect and redact PII before any external LLM call. | stated | "Never send raw PII to an external LLM." | high |
| FR-004 | The system shall checkpoint graph state per session in Postgres and allow a session to resume from its latest valid checkpoint. | stated | "State is checkpointed per session." | high |
| FR-005 | The system shall run the graph nodes intake_redaction, discovery, requirements, process_map, research, evaluator, risk_check, critic, human_review, and composer as typed stages. | stated | "Supervisor graph with nodes..." | high |
| FR-006 | The system shall return requirements grouped into goals, functional, non-functional, assumptions, constraints, and open_questions. | stated | "Return JSON matching the RequirementsDoc schema..." | high |
| FR-007 | The system shall represent each functional requirement as one testable sentence beginning with "The system shall..." and containing an acceptance criterion. | stated | "Every functional requirement is one testable sentence..." | high |
| FR-008 | The system shall tag each requirements item as stated or inferred and include supporting evidence for stated items. | stated | "Tag each item with the source..." | high |
| FR-009 | The system shall set confidence to low for requirements dependent on absent volume, error-rate, or cost data. | stated | "If volume, error rate or cost data is absent..." | high |
| FR-010 | The system shall attach source_id, quoted evidence, confidence, and support status to each research claim. | stated | "Every factual claim in research output must carry a source id..." | high |
| FR-011 | The system shall replace a research claim with "insufficient evidence" when the critic cannot verify adequate support. | stated | "If evidence is weak, output 'insufficient evidence'." | high |
| FR-012 | The system shall retry a failed responsible node no more than two times before routing the run to human review. | stated | "critic (max 2 retries, routes failures back to the responsible node)" | high |
| FR-013 | The system shall stream progress and human-review requests to the React client. | stated | "React frontend with streaming" | high |
| FR-014 | The system shall record prompt versions, model identifiers, retrieval settings, validation results, citations, critic decisions, and human decisions for each run. | inferred | Traceability required by prompt versioning, evaluation, and checkpoint constraints. | medium |
| FR-015 | The system shall enforce session and tenant filtering in application code around retrieval and persistence. | inferred | Required to prevent cross-session or cross-tenant evidence leakage. | medium |

## Non-Functional Requirements

| ID | Text | Source Type | Evidence | Confidence |
|---|---|---|---|---|
| NFR-001 | The system shall support pilot operation with an assumed ceiling of 10 concurrent sessions and a typical end-to-end completion time of 2 minutes. | inferred | Pilot-scale assumption confirmed during design. | low |
| NFR-002 | The system shall use Pydantic v2 validation at every node boundary and expose validation failures as explicit errors. | stated | "Each node has typed input/output schemas"; Pydantic v2 stack requirement. | high |
| NFR-003 | The system shall use local Ollama inference by default and shall require explicit configuration before using an external fallback provider. | inferred | Local-first deployment and privacy policy assumptions. | medium |
| NFR-004 | The system shall preserve enough provenance to reconstruct the final package from checkpointed node outputs without exposing raw PII to external telemetry. | inferred | Privacy, checkpointing, and observability constraints. | medium |
| NFR-005 | The system shall run prompt and golden-case evaluation checks in CI when a versioned prompt changes. | stated | "changing a prompt triggers the evaluation suite in CI." | high |
| NFR-006 | The system shall measure schema validity, citation support, unsupported-claim rate, retrieval quality, critic escape rate, human-review rate, p95 latency, and cost per session before reporting metrics. | inferred | AI-engineering completion evidence and the no-unmeasured-metrics constraint. | medium |

## Assumptions

- The first deployment is local Docker/self-hosted.
- The first access model is single-user; authentication and tenant administration are phase 7 work.
- Session data has a default 30-day retention class; the exact policy remains configurable.
- Research sources may include user-provided documents and approved connectors, but connector selection is not fixed in phase 1.
- The process-map contract supports a canonical graph representation and can later export to Mermaid and BPMN.
- Postgres is the system of record for application state, checkpoints, and retrieval metadata.

## Constraints

- Raw PII must never be sent to an external LLM.
- Uploaded and retrieved text is untrusted data and cannot authorize actions or alter system policy.
- No factual research claim may be presented without a verifiable source identifier.
- Unsupported or weakly supported evidence must be surfaced as "insufficient evidence."
- Secrets must come from environment configuration and never be hardcoded.
- Prompt templates are versioned files outside application code.
- The graph has a maximum of two critic-driven retries per responsible node.

## Open Questions

1. What exact session and trace retention duration should production use?
2. Which research connectors are approved for v1 beyond user-provided documents?
3. Should the first process-map export be Mermaid, BPMN, or both?
4. What reviewer roles and approval semantics are needed when authentication is introduced?
5. Which external model providers are approved for fallback after redaction?

## Phase 1 Acceptance Criteria

- The four product outputs and all graph stages are represented in the data and architecture contracts.
- Security and evidence constraints are explicit and testable.
- Each requirements item has an id, text, source type, evidence, and confidence.
- The architecture diagram shows application and component layers plus storage and model boundaries.
- No performance or quality metric is claimed as measured.
