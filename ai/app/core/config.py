from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import BeforeValidator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(value: Any) -> list[str] | str:
    if isinstance(value, str) and not value.startswith("["):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, list | str):
        return value
    raise ValueError(value)


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_prefix="AI_",
        env_ignore_empty=True,
        extra="ignore",
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Service"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    FRONTEND_HOST: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: Annotated[list[str] | str, BeforeValidator(parse_cors)] = []
    AI_PROVIDER: str = "openai"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str | None = None

    @computed_field
    @property
    def all_cors_origins(self) -> list[str]:
        origins = self.BACKEND_CORS_ORIGINS
        if isinstance(origins, str):
            origins = [origins]
        return [origin.rstrip("/") for origin in origins] + [self.FRONTEND_HOST.rstrip("/")]


settings = Settings()
