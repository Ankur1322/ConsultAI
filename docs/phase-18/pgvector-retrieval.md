# Phase 18: Durable pgvector retrieval

PostgreSQL sources now have a pgvector embedding column and HNSW cosine index.
Enable embedding generation with:

```powershell
$env:CONSULTAI_EMBEDDINGS_ENABLED = "true"
$env:CONSULTAI_EMBEDDING_MODEL = "nomic-embed-text"
```

The API asks Ollama for source and query embeddings, combines vector cosine
similarity with PostgreSQL full-text ranking, and falls back to the existing
lexical scorer when the embedding provider is unavailable. Embeddings with an
unexpected dimension are not persisted.
