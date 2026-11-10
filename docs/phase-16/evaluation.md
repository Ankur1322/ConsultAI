# Phase 16: Evaluation maturity

The evaluation corpus now includes five adversarial cases covering prompt
injection, poisoned documents, PII variants, contradictions, and citation
manipulation. The quality gate asserts the existing minimum rubric score of
`0.75`; changes that lower a complete, testable, grounded requirements output
below that threshold fail the test suite.

The adversarial cases are fixtures for the next provider-backed evaluation
stage, where each will be run through redaction, retrieval, citation checking,
and human-review routing.
