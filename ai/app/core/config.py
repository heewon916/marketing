import os
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
    KEYWORD_MODEL_PATH: str | None = None
    KEYWORD_MODEL_HF_REPO_ID: str = "Qwen/Qwen2.5-7B-Instruct-GGUF"
    KEYWORD_MODEL_HF_FILENAME: str = "qwen2.5-7b-instruct-q3_k_m.gguf"
    KEYWORD_MODEL_CTX_SIZE: int = 2048
    KEYWORD_MODEL_MAX_TOKENS: int = 64
    KEYWORD_MODEL_TEMPERATURE: float = 0.1
    KEYWORD_MODEL_TOP_P: float = 0.9
    KEYWORD_MODEL_THREADS: int = max((os.cpu_count() or 1) - 2, 1)
    KEYWORD_MODEL_GPU_LAYERS: int = 20
    KEYWORD_MODEL_ENABLED: bool = True
    KEYWORD_MODEL_TIMEOUT_SECONDS: float = 10.0

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

    @computed_field
    @property
    def keyword_model_path(self) -> Path | None:
        configured = self.KEYWORD_MODEL_PATH
        if not configured:
            return None
        candidate = Path(configured)
        if candidate.is_absolute():
            return candidate
        return ROOT_DIR.parent / candidate


settings = Settings()
