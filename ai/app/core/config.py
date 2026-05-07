import os
from pathlib import Path
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR.parent / ".env"
DEFAULT_ORIENTATION_MODEL_NAME = "vit"
DEFAULT_ORIENTATION_MODEL_WEIGHTS_PATH = (
    ROOT_DIR / "weights" / "model-vit-ang-loss.h5"
)
# Legacy local GGUF settings are kept for reference during the llama-server migration.
DEFAULT_KEYWORD_MODEL_PATH = ROOT_DIR / "models" / "qwen-gguf" / "model.gguf"
DEFAULT_KEYWORD_MODEL_HF_REPO_ID = "Qwen/Qwen2.5-7B-Instruct-GGUF"
DEFAULT_KEYWORD_MODEL_HF_FILENAME = "qwen2.5-7b-instruct-q3_k_m.gguf"
DEFAULT_KEYWORD_MODEL_TIMEOUT_SECONDS = 30.0
DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"
DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_CACHE_DIR = (
    ROOT_DIR / "models" / "canonical-keywords"
)
DEFAULT_CANONICAL_KEYWORD_EMBEDDING_DIM = 384


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
    LOG_INCLUDE_RAW_IDENTIFIERS: bool = True
    LOG_EVENT_PREVIEW_MAX_LEN: int = 200

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
    ORIENTATION_MODEL_DOWNLOAD_URL: str = (
        "https://drive.google.com/file/d/1sdmPmaDhivdHPfn9M9vAkTbiprbPq94e/view"
    )
    KEYWORD_MODEL_BASE_URL: str = "http://keyword-server:8001"
    KEYWORD_MODEL_CHAT_ENDPOINT: str = "/v1/chat/completions"
    KEYWORD_MODEL_API_KEY: str | None = None
    # Legacy local inference settings kept for rollback while FastAPI moves to llama-server.
    KEYWORD_MODEL_CTX_SIZE: int = 2048
    KEYWORD_MODEL_MAX_TOKENS: int = 64
    KEYWORD_MODEL_TEMPERATURE: float = 0.1
    KEYWORD_MODEL_TOP_P: float = 0.9
    KEYWORD_MODEL_THREADS: int = max((os.cpu_count() or 1) - 2, 1)
    KEYWORD_MODEL_GPU_LAYERS: int = 20
    KEYWORD_MODEL_ENABLED: bool = True
    KEYWORD_MODEL_TIMEOUT_SECONDS: float = DEFAULT_KEYWORD_MODEL_TIMEOUT_SECONDS
    CANONICAL_KEYWORD_RESOLVER_ENABLED: bool = True
    CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME: str = (
        DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME
    )
    CANONICAL_KEYWORD_EMBEDDING_MODEL_CACHE_DIR: Path = (
        DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_CACHE_DIR
    )
    CANONICAL_KEYWORD_EMBEDDING_DIM: int = (
        DEFAULT_CANONICAL_KEYWORD_EMBEDDING_DIM
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

settings = Settings()
