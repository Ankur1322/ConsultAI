import json
import os
from urllib.request import Request, urlopen


class EmbeddingError(RuntimeError):
    """Raised when the configured embedding provider cannot respond."""


def embed_text(text: str) -> list[float] | None:
    if os.getenv("CONSULTAI_EMBEDDINGS_ENABLED", "false").lower() != "true":
        return None
    base_url = os.getenv("CONSULTAI_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("CONSULTAI_EMBEDDING_MODEL", "nomic-embed-text")
    request = Request(
        f"{base_url}/api/embed",
        data=json.dumps({"model": model, "input": text}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urlopen(request, timeout=float(os.getenv("CONSULTAI_EMBEDDING_TIMEOUT_SECONDS", "15"))) as response:
            body = json.loads(response.read().decode())
    except (OSError, ValueError) as exc:
        raise EmbeddingError("Embedding provider request failed") from exc
    embeddings = body.get("embeddings")
    if not isinstance(embeddings, list) or not embeddings or not isinstance(embeddings[0], list):
        raise EmbeddingError("Embedding provider returned an invalid response")
    return [float(value) for value in embeddings[0]]
