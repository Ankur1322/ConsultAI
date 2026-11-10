# Production Retrieval Baseline

Docker/PostgreSQL retrieval now uses a session-scoped PostgreSQL full-text
index (`tsvector` plus GIN) as the lexical stage, followed by the existing
semantic-overlap scorer. This provides a real database-backed lexical
candidate stage without allowing cross-session documents into a query.

The retrieval service remains provider-pluggable. A future embedding provider
can replace `_semantic_overlap`, and a cross-encoder can rerank the bounded
candidate list. No semantic model quality is claimed until an embedding model
and reranker are benchmarked on the golden set.
