import json

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_SSL: bool = False
    DATABASE_SSL_VERIFY: bool = True
    DATABASE_CONNECT_TIMEOUT: int = 10

    cors_origins: str = "http://localhost:3000"
    supabase_url: str
    supabase_jwt_secret: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Return CORS origins as a list."""
        value = self.cors_origins.strip()
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


settings = Settings()  # pyright: ignore[reportCallIssue]
