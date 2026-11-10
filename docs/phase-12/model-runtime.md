# Phase 12: Model runtime

The requirements agent now supports an opt-in model execution path:

```powershell
$env:CONSULTAI_LLM_ENABLED = "true"
$env:CONSULTAI_MODEL_PROVIDER = "ollama"
$env:CONSULTAI_OLLAMA_MODEL = "llama3.2"
```

Ollama receives the versioned prompt with JSON mode enabled. The response is
validated against `RequirementsDoc`; invalid output is rejected rather than
silently treated as a successful result. Set `CONSULTAI_MODEL_PROVIDER=litellm`
and `CONSULTAI_LITELLM_MODEL` to use LiteLLM instead. The deterministic
implementation remains the default for offline operation and tests.
