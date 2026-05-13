from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # ── LLM Provider ──────────────────────────────────────────────────────────
    # Set to "openai" to use GPT, or "gemini" to use Google Gemini.
    LLM_PROVIDER: str = "openai"

    # ── OpenAI (used when LLM_PROVIDER=openai) ────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # ── Google Gemini (used when LLM_PROVIDER=gemini) ─────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"

    JWT_SECRET: str = "change-me-in-production"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    DB_PATH: Path = Path(__file__).parent.parent / "storage" / "app.db"
    SMTP_FROM_EMAIL: str = ""
    SMTP_APP_PASSWORD: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    PRODUCTION: bool = False  # Set to True in production to enforce HTTPS
    RESPONSE_TIMEOUT: int = 120  # Override via RESPONSE_TIMEOUT env var for stricter deployments

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
