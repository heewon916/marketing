from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR.parent / ".env"

DEFAULT_ORIENTATION_MODEL_NAME = "vit"
DEFAULT_ORIENTATION_MODEL_WEIGHTS_PATH = (
    ROOT_DIR / "weights" / "model-vit-ang-loss.h5"
)

DEFAULT_KEYWORD_MODEL_SERVER_PORT = 8001
DEFAULT_KEYWORD_MODEL_HOST_DIR = "./.models/keyword/qwen2-1.5b-instruct/q3_k_m"
DEFAULT_KEYWORD_MODEL_PATH = (
    ROOT_DIR / "models" / "qwen2-1.5b-instruct" / "q3_k_m" / "model.gguf"
)
DEFAULT_KEYWORD_MODEL_HF_REPO_ID = "Qwen/Qwen2-1.5B-Instruct-GGUF"
DEFAULT_KEYWORD_MODEL_HF_FILENAME = "qwen2-1_5b-instruct-q3_k_m.gguf"
DEFAULT_KEYWORD_MODEL_TIMEOUT_SECONDS = 60.0
DEFAULT_KEYWORD_MODEL_HEALTH_ENDPOINT = "/health"

DEFAULT_CAPTION_MODEL_SERVER_PORT = 8002
DEFAULT_CAPTION_MODEL_HOST_DIR = "./.models/caption/qwen2.5-7b-instruct/q3_k_m"
DEFAULT_CAPTION_MODEL_PATH = (
    ROOT_DIR / "models" / "qwen2.5-7b-instruct" / "q3_k_m" / "model.gguf"
)
DEFAULT_CAPTION_MODEL_HF_REPO_ID = "Qwen/Qwen2.5-7B-Instruct-GGUF"
DEFAULT_CAPTION_MODEL_HF_FILENAME = "qwen2.5-7b-instruct-q3_k_m.gguf"
DEFAULT_CAPTION_MODEL_TIMEOUT_SECONDS = 120.0
DEFAULT_CAPTION_MODEL_HEALTH_ENDPOINT = "/health"

DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME = "intfloat/multilingual-e5-small"
DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_CACHE_DIR = (
    ROOT_DIR / "models" / "canonical-keywords"
)
DEFAULT_CANONICAL_KEYWORD_EMBEDDING_DIM = 384


@dataclass(frozen=True)
class LlamaModelClientSettings:
    base_url: str
    chat_endpoint: str
    health_endpoint: str
    api_key: str | None
    timeout_seconds: float
    max_tokens: int
    temperature: float
    top_p: float
    enabled: bool


@dataclass(frozen=True)
class LlamaModelServerSettings:
    host_dir: str
    hf_repo_id: str
    hf_filename: str
    server_port: int
    ctx_size: int
    gpu_layers: int


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

    KEYWORD_MODEL_HOST_DIR: str = DEFAULT_KEYWORD_MODEL_HOST_DIR
    KEYWORD_MODEL_HF_REPO_ID: str = DEFAULT_KEYWORD_MODEL_HF_REPO_ID
    KEYWORD_MODEL_HF_FILENAME: str = DEFAULT_KEYWORD_MODEL_HF_FILENAME
    KEYWORD_MODEL_SERVER_PORT: int = DEFAULT_KEYWORD_MODEL_SERVER_PORT
    KEYWORD_MODEL_BASE_URL: str = (
        f"http://keyword-server:{DEFAULT_KEYWORD_MODEL_SERVER_PORT}"
    )
    KEYWORD_MODEL_CHAT_ENDPOINT: str = "/v1/chat/completions"
    KEYWORD_MODEL_HEALTH_ENDPOINT: str = DEFAULT_KEYWORD_MODEL_HEALTH_ENDPOINT
    KEYWORD_MODEL_API_KEY: str | None = None
    KEYWORD_MODEL_CTX_SIZE: int = 2048
    KEYWORD_MODEL_GPU_LAYERS: int = 20
    KEYWORD_MODEL_MAX_TOKENS: int = 64
    KEYWORD_MODEL_TEMPERATURE: float = 0.1
    KEYWORD_MODEL_TOP_P: float = 0.9
    KEYWORD_MODEL_ENABLED: bool = True
    KEYWORD_MODEL_TIMEOUT_SECONDS: float = DEFAULT_KEYWORD_MODEL_TIMEOUT_SECONDS

    CAPTION_MODEL_HOST_DIR: str = DEFAULT_CAPTION_MODEL_HOST_DIR
    CAPTION_MODEL_HF_REPO_ID: str = DEFAULT_CAPTION_MODEL_HF_REPO_ID
    CAPTION_MODEL_HF_FILENAME: str = DEFAULT_CAPTION_MODEL_HF_FILENAME
    CAPTION_MODEL_SERVER_PORT: int = DEFAULT_CAPTION_MODEL_SERVER_PORT
    CAPTION_MODEL_BASE_URL: str = (
        f"http://caption-server:{DEFAULT_CAPTION_MODEL_SERVER_PORT}"
    )
    CAPTION_MODEL_CHAT_ENDPOINT: str = "/v1/chat/completions"
    CAPTION_MODEL_HEALTH_ENDPOINT: str = DEFAULT_CAPTION_MODEL_HEALTH_ENDPOINT
    CAPTION_MODEL_API_KEY: str | None = None
    CAPTION_MODEL_CTX_SIZE: int = 2048
    CAPTION_MODEL_GPU_LAYERS: int = 20
    CAPTION_MODEL_MAX_TOKENS: int = 256
    CAPTION_MODEL_TEMPERATURE: float = 0.7
    CAPTION_MODEL_TOP_P: float = 0.9
    CAPTION_MODEL_ENABLED: bool = True
    CAPTION_MODEL_TIMEOUT_SECONDS: float = DEFAULT_CAPTION_MODEL_TIMEOUT_SECONDS

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

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug_value(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"debug", "local", "dev", "development"}:
                return True
        return value

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
    def keyword_model_client(self) -> LlamaModelClientSettings:
        return LlamaModelClientSettings(
            base_url=self.KEYWORD_MODEL_BASE_URL.rstrip("/"),
            chat_endpoint=self.KEYWORD_MODEL_CHAT_ENDPOINT,
            health_endpoint=self.KEYWORD_MODEL_HEALTH_ENDPOINT,
            api_key=self.KEYWORD_MODEL_API_KEY,
            timeout_seconds=self.KEYWORD_MODEL_TIMEOUT_SECONDS,
            max_tokens=self.KEYWORD_MODEL_MAX_TOKENS,
            temperature=self.KEYWORD_MODEL_TEMPERATURE,
            top_p=self.KEYWORD_MODEL_TOP_P,
            enabled=self.KEYWORD_MODEL_ENABLED,
        )

    @computed_field
    @property
    def caption_model_client(self) -> LlamaModelClientSettings:
        return LlamaModelClientSettings(
            base_url=self.CAPTION_MODEL_BASE_URL.rstrip("/"),
            chat_endpoint=self.CAPTION_MODEL_CHAT_ENDPOINT,
            health_endpoint=self.CAPTION_MODEL_HEALTH_ENDPOINT,
            api_key=self.CAPTION_MODEL_API_KEY,
            timeout_seconds=self.CAPTION_MODEL_TIMEOUT_SECONDS,
            max_tokens=self.CAPTION_MODEL_MAX_TOKENS,
            temperature=self.CAPTION_MODEL_TEMPERATURE,
            top_p=self.CAPTION_MODEL_TOP_P,
            enabled=self.CAPTION_MODEL_ENABLED,
        )

    @computed_field
    @property
    def keyword_model_server(self) -> LlamaModelServerSettings:
        return LlamaModelServerSettings(
            host_dir=self.KEYWORD_MODEL_HOST_DIR,
            hf_repo_id=self.KEYWORD_MODEL_HF_REPO_ID,
            hf_filename=self.KEYWORD_MODEL_HF_FILENAME,
            server_port=self.KEYWORD_MODEL_SERVER_PORT,
            ctx_size=self.KEYWORD_MODEL_CTX_SIZE,
            gpu_layers=self.KEYWORD_MODEL_GPU_LAYERS,
        )

    @computed_field
    @property
    def caption_model_server(self) -> LlamaModelServerSettings:
        return LlamaModelServerSettings(
            host_dir=self.CAPTION_MODEL_HOST_DIR,
            hf_repo_id=self.CAPTION_MODEL_HF_REPO_ID,
            hf_filename=self.CAPTION_MODEL_HF_FILENAME,
            server_port=self.CAPTION_MODEL_SERVER_PORT,
            ctx_size=self.CAPTION_MODEL_CTX_SIZE,
            gpu_layers=self.CAPTION_MODEL_GPU_LAYERS,
        )


settings = Settings()
