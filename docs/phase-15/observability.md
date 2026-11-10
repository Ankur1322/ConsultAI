# Phase 15: Privacy-safe observability

The API exposes `GET /metrics` with aggregate counters for requests, model
calls, retrieval calls, citation support, unsupported evidence, and human
reviews. Request logs include method, path, status, and latency only; request
bodies and PII are not logged. The counters are process-local until a metrics
exporter (Langfuse, LangSmith, or Prometheus) is selected for deployment.
