# Production PII Redaction

The redaction service attempts Presidio Analyzer and Anonymizer first. If the
optional Presidio runtime or its language model is unavailable, the service
uses the tested local patterns for email, phone, and credit-card values and
does not silently expose the original value.

PII redaction occurs before session descriptions and source documents enter
the application stores or model/retrieval pipeline. The service records only
counts and entity types as metadata.
