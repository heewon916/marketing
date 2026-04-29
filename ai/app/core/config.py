from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "AI Service"
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "DEBUG"
    PROVIDER: str = "openai"
    DEFAULT_MODEL: str = "gpt-4o-mini"
    OPENAI_API_KEY: str | None = None

    DEBUG: bool = True

    POSTGRES_HOST: str = "project-postgres"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    REDIS_HOST: str = "project-redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    REDIS_DB: int = 0

    SESSION_TTL_SECONDS: int = 3600

    S3_SECRET_KEY: str | None = None
    S3_ACCESS_KEY: str | None = None
    S3_BUCKET_NAME: str | None = None
    S3_REGION: str | None = None
    CLOUDFRONT_DOMAIN: str | None = None
    ORIENTATION_MODEL_WEIGHTS_PATH: str | None = None
    ORIENTATION_MODEL_NAME: str = "vit"
    ORIENTATION_MODEL_DOWNLOAD_URL: str = (
        "https://drive.google.com/file/d/1sdmPmaDhivdHPfn9M9vAkTbiprbPq94e/view"
    )

    @computed_field
    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    @property
    def redis_url(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @computed_field
    @property
    def s3_configured(self) -> bool:
        return all(
            [
                self.S3_SECRET_KEY,
                self.S3_ACCESS_KEY,
                self.S3_BUCKET_NAME,
                self.S3_REGION,
            ]
        )

    @computed_field
    @property
    def orientation_model_weights_path(self) -> Path:
        configured = self.ORIENTATION_MODEL_WEIGHTS_PATH
        if configured:
            candidate = Path(configured)
            if candidate.is_absolute():
                return candidate
            return ROOT_DIR.parent / candidate
        return ROOT_DIR / "weights" / "model-vit-ang-loss.h5"


settings = Settings()
