import json
import os
from urllib.error import URLError
from urllib.request import Request, urlopen


class ModelRuntimeError(RuntimeError):
    """Raised when an enabled model provider cannot return valid output."""


def generate_json(prompt: str) -> dict | None:
    if os.getenv("CONSULTAI_LLM_ENABLED", "false").lower() != "true":
        return None
    provider = os.getenv("CONSULTAI_MODEL_PROVIDER", "ollama").lower()
    if provider == "litellm":
        try:
            from litellm import completion

            response = completion(
                model=os.environ["CONSULTAI_LITELLM_MODEL"],
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                timeout=float(os.getenv("CONSULTAI_MODEL_TIMEOUT_SECONDS", "30")),
            )
            content = response.choices[0].message.content
            result = json.loads(content)
        except (KeyError, IndexError, TypeError, ValueError, ImportError, OSError) as exc:
            raise ModelRuntimeError("LiteLLM fallback failed") from exc
        if not isinstance(result, dict):
            raise ModelRuntimeError("LiteLLM JSON response must be an object")
        return result
    if provider != "ollama":
        raise ModelRuntimeError(f"Unsupported model provider: {provider}")
    base_url = os.getenv("CONSULTAI_OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    model = os.getenv("CONSULTAI_OLLAMA_MODEL", "llama3.2")
    payload = json.dumps({"model": model, "prompt": prompt, "format": "json", "stream": False}).encode()
    request = Request(f"{base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urlopen(request, timeout=float(os.getenv("CONSULTAI_MODEL_TIMEOUT_SECONDS", "30"))) as response:
            body = json.loads(response.read().decode())
    except (OSError, ValueError, URLError) as exc:
        raise ModelRuntimeError("Ollama model request failed") from exc
    try:
        result = json.loads(body["response"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ModelRuntimeError("Ollama returned invalid JSON") from exc
    if not isinstance(result, dict):
        raise ModelRuntimeError("Ollama JSON response must be an object")
    return result
