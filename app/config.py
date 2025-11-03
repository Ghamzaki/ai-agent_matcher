import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data.db")

    # --- Mailtrap API (no IMAP anymore) ---
    MAILTRAP_API_URL: str = os.getenv("MAILTRAP_API_URL", "https://sandbox.api.mailtrap.io/api/send")
    MAILTRAP_API_TOKEN: str = os.getenv("MAILTRAP_API_TOKEN", "")
    MAILTRAP_INBOX_ID: str = os.getenv("MAILTRAP_INBOX_ID", "")

    # --- Transaction polling ---
    TRANSACTIONS_POLL_INTERVAL_SECONDS: int = int(os.getenv("TRANSACTIONS_POLL_INTERVAL_SECONDS", "900"))
    TRANSACTIONS_SOURCE: str = os.getenv("TRANSACTIONS_SOURCE", "sample")
    TRANSACTIONS_API_URL: str = os.getenv("TRANSACTIONS_API_URL", "")
    TRANSACTIONS_API_TOKEN: str = os.getenv("TRANSACTIONS_API_TOKEN", "")

    # --- Telex (notifications) ---
    TELEX_WEBHOOK_URL: str = os.getenv("TELEX_WEBHOOK_URL", "")
    TELEX_API_TOKEN: str = os.getenv("TELEX_API_TOKEN", "")
    TELEX_CHANNEL_ID: str = os.getenv("TELEX_CHANNEL_ID", "demo-channel")

    # --- LLM enrichment ---
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # --- Admin ---
    TELEX_AGENT_ADMIN: bool = os.getenv("TELEX_AGENT_ADMIN", "") == "1"


settings = Settings()