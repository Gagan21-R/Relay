"""All settings come from the environment (.env). Mock mode lets the whole app run with no external keys."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../.env"), env_file_encoding="utf-8", extra="ignore")

    app_name: str = "RELAY"
    environment: str = "development"

    # Mock mode: mock LLM, mock embeddings, mock SMS/voice. Forced on when no Gemini key is set.
    relay_mock_mode: bool = True

    # PostgreSQL in Docker; a local SQLite file when Postgres is not available (same SQLAlchemy models).
    database_url: str = "sqlite:///./relay_dev.db"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"
    gemini_embed_model: str = "text-embedding-004"

    # SMS / voice provider: "mock" (built-in simulator), "twilio", "exotel", "msg91"
    sms_provider: str = "mock"
    sms_from_number: str = "+910000000000"
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""

    # Phone numbers are stored hashed with this salt and shown masked.
    phone_hash_salt: str = "change-me"

    cors_origins: str = "http://localhost:5180,http://127.0.0.1:5180"

    @property
    def mock(self) -> bool:
        """Mock mode is on when asked for, or when there is no Gemini key to use."""
        return self.relay_mock_mode or not self.gemini_api_key

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
