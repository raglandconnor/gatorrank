from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    DATABASE_URL: str
    DATABASE_SSL: bool = False
    DATABASE_SSL_VERIFY: bool = True
    DATABASE_CONNECT_TIMEOUT: int = 10
    cors_origins: str = "http://localhost:3000"

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


settings = Settings()  # pyright: ignore[reportCallIssue]
