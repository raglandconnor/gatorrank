import json
from functools import lru_cache

from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment variables:
    # Database (Supabase)
    DATABASE_URL: str
    DATABASE_SSL: bool = False
    DATABASE_SSL_VERIFY: bool = True
    DATABASE_JWT_SECRET: str
    DATABASE_CONNECT_TIMEOUT: int = 10
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        value = self.CORS_ORIGINS.strip()
        if not value:
            return []
        if value.startswith("["):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return [
                        str(origin).strip() for origin in parsed if str(origin).strip()
                    ]
            except json.JSONDecodeError:
                pass
        return [origin.strip() for origin in value.split(",") if origin.strip()]

    @property
    def async_database_url(self) -> str:
        """Return DATABASE_URL normalized for async SQLAlchemy runtime."""
        value = self.DATABASE_URL.strip()
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+asyncpg://", 1)
        return value

    @property
    def sync_database_url(self) -> str:
        """Return DATABASE_URL normalized for sync migration tooling."""
        value = self.DATABASE_URL.strip()
        if value.startswith("postgresql+asyncpg://"):
            return value.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg://", 1)
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore[reportCallIssue]


def load_settings_or_exit() -> Settings:
    try:
        return get_settings()
    except ValidationError as exc:
        missing: list[str] = []
        invalid: list[str] = []

        for err in exc.errors():
            field_name = ".".join(str(part) for part in err.get("loc", ()))
            if err.get("type") == "missing":
                missing.append(field_name)
            else:
                invalid.append(f"{field_name}: {err.get('msg', 'Invalid value')}")

        message_lines = ["Configuration error: backend startup aborted."]
        if missing:
            message_lines.append(f"Missing env vars: {', '.join(sorted(missing))}")
        if invalid:
            message_lines.append("Invalid env vars:")
            message_lines.extend(f"  - {item}" for item in invalid)
        message_lines.append("Check your environment variables or .env file and retry.")
        raise SystemExit("\n".join(message_lines)) from None
