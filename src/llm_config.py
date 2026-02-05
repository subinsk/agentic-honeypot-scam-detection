"""
LLM configurator: select provider and resolve API key, base URL, and model.
Supports OpenAI, Claude (via OpenRouter), Grok (xAI), Gemini (via OpenRouter),
GitHub Models, Groq, DeepSeek, and custom OpenAI-compatible endpoints.

Global priority order for fallback: Groq → OpenRouter → GitHub → rest.
If one provider fails, the next is tried until one succeeds.
"""
from enum import Enum
from typing import NamedTuple

from src.config import settings


class LLMProvider(str, Enum):
    """Supported LLM providers (all use OpenAI-compatible chat completions)."""
    OLLAMA = "ollama"     # Local Ollama (no API key); set OLLAMA_BASE_URL for local testing
    OPENAI = "openai"
    CLAUDE = "claude"      # Anthropic via OpenRouter
    GROK = "grok"         # xAI
    GEMINI = "gemini"     # Google via OpenRouter
    GITHUB = "github"     # GitHub Models (PAT with models:read) – free for prototyping
    GROQ = "groq"         # High speed, free open-weights (Llama 4 Scout, Mixtral)
    OPENROUTER = "openrouter"  # 500+ models, use :free for Llama/Mistral without credit card
    DEEPSEEK = "deepseek"  # Value option when outgrowing free tiers


# Global priority: Ollama first when set (local testing), then Groq, OpenRouter, etc.
PROVIDER_PRIORITY: tuple[LLMProvider, ...] = (
    LLMProvider.OLLAMA,
    LLMProvider.GROQ,
    LLMProvider.OPENROUTER,
    LLMProvider.GITHUB,
    LLMProvider.OPENAI,
    LLMProvider.CLAUDE,
    LLMProvider.GEMINI,
    LLMProvider.GROK,
    LLMProvider.DEEPSEEK,
)


# Default base URLs (OpenAI-compatible)
DEFAULT_BASE_URLS = {
    LLMProvider.OLLAMA: "http://localhost:11434/v1",
    LLMProvider.OPENAI: "https://api.openai.com/v1",
    LLMProvider.CLAUDE: "https://openrouter.ai/api/v1",
    LLMProvider.GROK: "https://api.x.ai/v1",
    LLMProvider.GEMINI: "https://openrouter.ai/api/v1",
    LLMProvider.GITHUB: "https://models.github.ai/inference",
    LLMProvider.GROQ: "https://api.groq.com/openai/v1",
    LLMProvider.OPENROUTER: "https://openrouter.ai/api/v1",
    LLMProvider.DEEPSEEK: "https://api.deepseek.com/v1",
}

# Free-tier / local defaults
# For local testing: deepseek-r1:8b (default), llama3, llama3.2; override with LLM_MODEL
DEFAULT_MODELS = {
    LLMProvider.OLLAMA: "deepseek-r1:8b",  # reasoning model; or llama3, llama3.2
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.CLAUDE: "meta-llama/llama-3.3-70b-instruct:free",   # Free via OpenRouter
    LLMProvider.GROK: "grok-2-latest",
    LLMProvider.GEMINI: "google/gemini-2.0-flash-exp:free",         # Free via OpenRouter
    LLMProvider.GITHUB: "openai/gpt-4o",                             # Free for prototyping
    LLMProvider.GROQ: "llama-3.3-70b-versatile",   # Free, fast, high quality (best for hackathon)
    LLMProvider.OPENROUTER: "meta-llama/llama-3.3-70b-instruct:free",
    LLMProvider.DEEPSEEK: "deepseek-chat",
}


class LLMClientConfig(NamedTuple):
    """Resolved config for creating an OpenAI-compatible client."""
    api_key: str
    base_url: str | None
    model: str


# Which settings field holds the comma-separated keys for each provider
_PROVIDER_KEYS_FIELD = {
    LLMProvider.OPENAI: "openai_api_keys",
    LLMProvider.CLAUDE: "openrouter_api_keys",
    LLMProvider.GROK: "xai_api_keys",
    LLMProvider.GEMINI: "openrouter_api_keys",
    LLMProvider.GITHUB: "github_api_keys",
    LLMProvider.GROQ: "groq_api_keys",
    LLMProvider.OPENROUTER: "openrouter_api_keys",
    LLMProvider.DEEPSEEK: "deepseek_api_keys",
}


def _get_provider_api_keys(provider: LLMProvider) -> list[str]:
    """Return list of API keys for the provider. Ollama has no key (uses OLLAMA_BASE_URL)."""
    if provider == LLMProvider.OLLAMA:
        return []
    field = _PROVIDER_KEYS_FIELD.get(provider)
    if not field:
        return []
    raw = getattr(settings, field, "") or ""
    if not raw or not isinstance(raw, str):
        return []
    keys = [k.strip() for k in raw.split(",") if k.strip()]
    return keys


def get_configured_providers_in_priority() -> list[tuple[LLMProvider, LLMClientConfig]]:
    """
    Return (provider, config) in priority order. Ollama is added first when OLLAMA_BASE_URL is set
    (no API key). Other providers require at least one key. Each entry is tried in turn until one succeeds.
    When USE_LOCAL_LLM_ONLY=true, only Ollama is used (no cloud APIs).
    """
    out: list[tuple[LLMProvider, LLMClientConfig]] = []
    use_local_only = getattr(settings, "use_local_llm_only", False)

    # Ollama: enabled by OLLAMA_BASE_URL only (no key)
    ollama_url = (getattr(settings, "ollama_base_url", None) or "").strip()
    if ollama_url:
        base = ollama_url.rstrip("/")
        if not base.endswith("/v1"):
            base = f"{base}/v1" if base else "http://localhost:11434/v1"
        model = getattr(settings, "llm_model", None) or DEFAULT_MODELS.get(LLMProvider.OLLAMA) or "deepseek-r1:8b"
        out.append((LLMProvider.OLLAMA, LLMClientConfig(api_key="ollama", base_url=base, model=model)))

    if use_local_only:
        return out

    for provider in PROVIDER_PRIORITY:
        if provider == LLMProvider.OLLAMA:
            continue
        keys = _get_provider_api_keys(provider)
        base_url = getattr(settings, "llm_base_url", None) or DEFAULT_BASE_URLS.get(provider)
        model = getattr(settings, "llm_model", None) or DEFAULT_MODELS.get(provider) or "gpt-4o-mini"
        for api_key in keys:
            out.append((provider, LLMClientConfig(api_key=api_key, base_url=base_url, model=model)))
    return out


def has_llm_configured() -> bool:
    """True if any configured provider has an API key set (for optional LLM features)."""
    return len(get_configured_providers_in_priority()) > 0
