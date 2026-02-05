"""Application configuration from environment."""
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_secret_key: str
    guvi_callback_url: str = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"

    # LLM: per-provider arrays (comma-separated). Try order: Groq keys, then OpenRouter, then GitHub, etc.
    # Example: GROQ_API_KEYS=gsk_xxx,gsk_yyy  or  OPENROUTER_API_KEYS=sk-or-xxx,sk-or-yyy
    groq_api_keys: str = ""
    openrouter_api_keys: str = ""
    github_api_keys: str = ""
    openai_api_keys: str = ""
    xai_api_keys: str = ""
    deepseek_api_keys: str = ""
    # Local Ollama (no API key needed). Set to e.g. http://localhost:11434/v1 for local testing.
    ollama_base_url: str = ""
    llm_model: str = ""
    llm_base_url: str | None = None
    # When True, use ONLY local Ollama (ignore Groq, OpenRouter, etc.). Good for dev without API keys.
    use_local_llm_only: bool = False
    # Speed optimization: disable slow LLM confirmation in scam detection (heuristics only). Faster for production.
    disable_scam_llm_confirm: bool = False

    # Optional: path to file with extra scam keywords (one word/phrase per line). Used by scam_detection.
    scam_keywords_file: str = ""

    # Logging (production-grade)
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_format: str = "json"  # "json" for production (structured), "console" for dev
    log_file: str | None = None  # optional path; if set, logs also written to file with rotation

    @model_validator(mode="after")
    def require_api_secret_key(self):
        if not self.api_secret_key or self.api_secret_key == "change-me-in-production":
            raise ValueError(
                "API_SECRET_KEY must be set in .env and must not be the default placeholder. "
                "Copy .env.example to .env and set a secure API_SECRET_KEY."
            )
        return self


settings = Settings()
