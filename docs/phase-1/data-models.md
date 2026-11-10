# ConsultAI Phase 1 Data Models

The following are logical Pydantic v2 contracts. Implementation belongs to phase 2 and later; field names are stable identifiers for graph state and API payloads.

## Session

| Field | Type | Notes |
|---|---|---|
| id | UUID | Session and checkpoint key |
| vertical | invoice_to_pay \| customer_support | V1 scope |
| status | draft \| running \| review \| completed \| failed | Lifecycle state |
| created_at | datetime | UTC |
| updated_at | datetime | UTC |
| retention_class | string | Policy-controlled retention |
| prompt_versions | map[string, string] | Prompt id to version |
| model_versions | map[string, string] | Provider/model id to version |

## IntakeDocument

| Field | Type | Notes |
|---|---|---|
| id | UUID | Document identifier |
| session_id | UUID | Session boundary |
| content_hash | string | Deduplication and provenance |
| source_name | string | User-visible label |
| source_type | upload \| text \| connector | Origin |
| redaction_status | pending \| completed \| failed | PII boundary |
| redaction_count | integer | Non-sensitive aggregate |
| redacted_text_ref | string | Internal storage reference |

## DiscoveryAnswers

| Field | Type | Notes |
|---|---|---|
| question_id | string | Stable question identifier |
| answer | string \| null | User-provided answer |
| status | answered \| unknown \| skipped | Explicit uncertainty |
| confidence | low \| medium \| high | Answer confidence |
| evidence | string \| null | Supporting phrase when available |

## RequirementItem

| Field | Type | Notes |
|---|---|---|
| id | string | Stable item identifier |
| text | string | Requirement or statement |
| source_type | stated \| inferred | Origin classification |
| evidence | string \| null | Supporting phrase |
| confidence | low \| medium \| high | Confidence |
| acceptance_criterion | string \| null | Required for functional items |

## RequirementsDoc

Contains `goals`, `functional`, `non_functional`, `assumptions`, `constraints`, and `open_questions`, each represented by `RequirementItem` or an equivalent typed item contract.

## ProcessMap

| Field | Type | Notes |
|---|---|---|
| nodes | ProcessNode[] | Activities, decisions, events, or handoffs |
| edges | ProcessEdge[] | Directed transitions |
| actors | Actor[] | Roles or teams |
| systems | SystemRef[] | Applications and external systems |
| exceptions | ExceptionPath[] | Failure and alternate paths |
| unresolved_steps | string[] | Missing or ambiguous details |
| export_formats | string[] | Mermaid and/or BPMN when enabled |

## ResearchSummary

| Field | Type | Notes |
|---|---|---|
| claims | ResearchClaim[] | One record per factual claim |
| sources | SourceRecord[] | Source registry |
| unresolved_claims | string[] | Claims marked insufficient evidence |

Each `ResearchClaim` includes `claim_id`, `text`, `source_id`, `quoted_evidence`, `confidence`, and `support_status` (`supported`, `conflicting`, or `insufficient_evidence`).

## AIOpportunity

Each opportunity includes `id`, `title`, `process_step`, `rationale`, `rank`, `feasibility`, `value_evidence`, `risks`, `controls`, `human_oversight`, and `confidence`. Value ranges are optional and must be evidence-backed.

## ReviewDecision and RunEvent

`ReviewDecision` records `target_id`, `action`, `reason`, `reviewer_ref`, `timestamp`, and `resume_from_node`. `RunEvent` records node status, prompt/model versions, validation outcome, retry count, redaction aggregates, and error details without raw PII.
