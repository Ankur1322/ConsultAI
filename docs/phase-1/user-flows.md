# ConsultAI Phase 1 User Flows

## Flow 1: Create an analysis

1. The user starts a session.
2. The user selects invoice-to-pay or customer-support.
3. The user enters a process description and optionally uploads documents.
4. The system acknowledges that uploaded text is untrusted data.
5. `intake_redaction` detects and redacts PII, records redaction metadata, and creates the safe working corpus.
6. `discovery` asks bounded questions for missing actors, systems, exceptions, controls, and measures.
7. The user answers questions or marks them unknown.
8. The graph streams progress while `requirements`, `process_map`, `research`, `evaluator`, and `risk_check` run.
9. `critic` validates structure, evidence, citations, and rubric results.
10. The system composes a reviewable result package.

## Flow 2: Human review

1. The critic identifies a material defect, unsupported evidence, unresolved ambiguity, or exhausted retry budget.
2. LangGraph interrupts the run and persists the review request.
3. The frontend shows the target item, evidence, failure reason, and available decisions.
4. The reviewer accepts, edits, rejects, or requests a rerun with additional context.
5. The decision is persisted with reviewer metadata and the graph resumes from the appropriate checkpoint.

## Flow 3: Resume and inspect

1. The user reopens a session.
2. The API loads the latest checkpoint and run status.
3. The user can inspect node outputs, citations, assumptions, redaction counts, and review decisions.
4. The user resumes an interrupted run or views the completed package without rerunning successful nodes.

## Flow 4: Evidence failure

1. Retrieval returns weak or conflicting evidence.
2. Research marks the affected claim for verification.
3. The critic checks source support and citation alignment.
4. If support remains inadequate, the claim is rendered as "insufficient evidence."
5. The user sees the unresolved claim and may provide an approved source or send it to human review.

## Flow 5: Unsafe or malformed input

1. The intake boundary identifies PII, prompt-injection-like text, invalid file content, or unsupported input.
2. PII is redacted where possible; invalid content produces an explicit error.
3. The content is retained only as untrusted evidence, never as executable instruction.
4. The user receives a clear action: edit input, remove a file, answer a question, or request review.
