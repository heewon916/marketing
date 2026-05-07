import pytest

from app.core.config import (
    DEFAULT_CANONICAL_KEYWORD_EMBEDDING_DIM,
    DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_CACHE_DIR,
    DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME,
    DEFAULT_KEYWORD_MODEL_HF_FILENAME,
    DEFAULT_KEYWORD_MODEL_HF_REPO_ID,
    DEFAULT_KEYWORD_MODEL_PATH,
    DEFAULT_KEYWORD_MODEL_TIMEOUT_SECONDS,
    DEFAULT_ORIENTATION_MODEL_NAME,
    DEFAULT_ORIENTATION_MODEL_WEIGHTS_PATH,
    Settings,
)


@pytest.fixture
def env_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_DB", "testdb")
    monkeypatch.setenv("POSTGRES_USER", "tester")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("REDIS_PASSWORD", "rsecret")
    monkeypatch.setenv("SESSION_TTL_SECONDS", "1800")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("S3_ACCESS_KEY", "access")
    monkeypatch.setenv("S3_SECRET_KEY", "secret")
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")
    monkeypatch.setenv("S3_REGION", "ap-northeast-2")
    monkeypatch.setenv("CLOUDFRONT_DOMAIN", "cdn.example.com")
    monkeypatch.setenv("KEYWORD_MODEL_CTX_SIZE", "4096")
    monkeypatch.setenv("KEYWORD_MODEL_MAX_TOKENS", "32")
    monkeypatch.setenv("KEYWORD_MODEL_TEMPERATURE", "0.2")
    monkeypatch.setenv("KEYWORD_MODEL_TOP_P", "0.85")
    monkeypatch.setenv("KEYWORD_MODEL_THREADS", "6")
    monkeypatch.setenv("KEYWORD_MODEL_GPU_LAYERS", "12")
    monkeypatch.setenv("KEYWORD_MODEL_ENABLED", "true")
    monkeypatch.setenv("CANONICAL_KEYWORD_RESOLVER_ENABLED", "true")
    monkeypatch.setenv(
        "CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME",
        "intfloat/multilingual-e5-small",
    )
    monkeypatch.setenv("CANONICAL_KEYWORD_EMBEDDING_DIM", "384")


def test_settings_parses_infra_fields(env_setup: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.POSTGRES_HOST == "project-postgres"
    assert settings.POSTGRES_PORT == 5432
    assert settings.REDIS_HOST == "project-redis"
    assert settings.REDIS_PORT == 6379
    assert settings.REDIS_DB == 0
    assert settings.SESSION_TTL_SECONDS == 1800
    assert settings.DEBUG is True
    assert settings.LOG_INCLUDE_RAW_IDENTIFIERS is True
    assert settings.LOG_EVENT_PREVIEW_MAX_LEN == 200
    assert settings.KEYWORD_MODEL_CTX_SIZE == 4096
    assert settings.KEYWORD_MODEL_MAX_TOKENS == 32
    assert settings.KEYWORD_MODEL_TEMPERATURE == 0.2
    assert settings.KEYWORD_MODEL_TOP_P == 0.85
    assert settings.KEYWORD_MODEL_THREADS == 6
    assert settings.KEYWORD_MODEL_GPU_LAYERS == 12
    assert settings.KEYWORD_MODEL_ENABLED is True
    assert settings.CANONICAL_KEYWORD_RESOLVER_ENABLED is True
    assert settings.CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME == "intfloat/multilingual-e5-small"
    assert settings.CANONICAL_KEYWORD_EMBEDDING_DIM == 384


def test_postgres_dsn_format(env_setup: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.postgres_dsn == (
        "postgresql+asyncpg://tester:secret@project-postgres:5432/testdb"
    )


def test_redis_url_with_password(env_setup: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.redis_url == "redis://:rsecret@project-redis:6379/0"


def _set_required_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("POSTGRES_USER", "u")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p")


def test_redis_url_without_password(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.delenv("REDIS_HOST", raising=False)
    monkeypatch.delenv("REDIS_PORT", raising=False)
    monkeypatch.delenv("REDIS_DB", raising=False)
    monkeypatch.delenv("REDIS_PASSWORD", raising=False)

    settings = Settings(_env_file=None)

    assert settings.redis_url == "redis://project-redis:6379/0"


def test_default_container_hosts_and_ports(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("POSTGRES_PORT", raising=False)
    monkeypatch.delenv("REDIS_HOST", raising=False)
    monkeypatch.delenv("REDIS_PORT", raising=False)

    settings = Settings(_env_file=None)

    assert settings.POSTGRES_HOST == "project-postgres"
    assert settings.POSTGRES_PORT == 5432
    assert settings.REDIS_HOST == "project-redis"
    assert settings.REDIS_PORT == 6379


def test_hosts_and_ports_can_still_be_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.setenv("POSTGRES_HOST", "test_pg")
    monkeypatch.setenv("POSTGRES_PORT", "6543")
    monkeypatch.setenv("REDIS_HOST", "test_redis")
    monkeypatch.setenv("REDIS_PORT", "6380")

    settings = Settings(_env_file=None)

    assert settings.POSTGRES_HOST == "test_pg"
    assert settings.POSTGRES_PORT == 6543
    assert settings.REDIS_HOST == "test_redis"
    assert settings.REDIS_PORT == 6380


def test_redis_db_defaults_to_zero_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.delenv("REDIS_DB", raising=False)

    settings = Settings(_env_file=None)

    assert settings.REDIS_DB == 0
    assert settings.redis_url.endswith("/0")


def test_settings_load_from_env_file_with_only_shared_db_vars(tmp_path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "POSTGRES_DB=testdb",
                "POSTGRES_USER=tester",
                "POSTGRES_PASSWORD=secret",
                "REDIS_PASSWORD=rsecret",
            ]
        ),
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.POSTGRES_HOST == "project-postgres"
    assert settings.POSTGRES_PORT == 5432
    assert settings.REDIS_HOST == "project-redis"
    assert settings.REDIS_PORT == 6379
    assert settings.REDIS_DB == 0
    assert settings.postgres_dsn == (
        "postgresql+asyncpg://tester:secret@project-postgres:5432/testdb"
    )
    assert settings.redis_url == "redis://:rsecret@project-redis:6379/0"


def test_s3_configured_when_required_fields_exist(env_setup: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.s3_configured is True
    assert settings.CLOUDFRONT_DOMAIN == "cdn.example.com"


def test_model_defaults_resolve_without_env(env_setup: None) -> None:
    assert DEFAULT_ORIENTATION_MODEL_NAME == "vit"
    assert DEFAULT_ORIENTATION_MODEL_WEIGHTS_PATH.name == "model-vit-ang-loss.h5"
    assert DEFAULT_KEYWORD_MODEL_PATH.name == "model.gguf"
    assert DEFAULT_KEYWORD_MODEL_HF_REPO_ID == "Qwen/Qwen2.5-7B-Instruct-GGUF"
    assert DEFAULT_KEYWORD_MODEL_HF_FILENAME == "qwen2.5-7b-instruct-q3_k_m.gguf"
    assert DEFAULT_KEYWORD_MODEL_TIMEOUT_SECONDS == 30.0
    assert DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME == "intfloat/multilingual-e5-small"
    assert DEFAULT_CANONICAL_KEYWORD_EMBEDDING_MODEL_CACHE_DIR.name == "canonical-keywords"
    assert DEFAULT_CANONICAL_KEYWORD_EMBEDDING_DIM == 384


def test_model_tunable_env_vars_are_applied(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.setenv("KEYWORD_MODEL_CTX_SIZE", "1024")
    monkeypatch.setenv("KEYWORD_MODEL_MAX_TOKENS", "16")
    monkeypatch.setenv("KEYWORD_MODEL_TEMPERATURE", "0.3")
    monkeypatch.setenv("KEYWORD_MODEL_TOP_P", "0.75")
    monkeypatch.setenv("KEYWORD_MODEL_THREADS", "3")
    monkeypatch.setenv("KEYWORD_MODEL_GPU_LAYERS", "8")
    monkeypatch.setenv("KEYWORD_MODEL_ENABLED", "false")

    settings = Settings(_env_file=None)

    assert settings.KEYWORD_MODEL_CTX_SIZE == 1024
    assert settings.KEYWORD_MODEL_MAX_TOKENS == 16
    assert settings.KEYWORD_MODEL_TEMPERATURE == 0.3
    assert settings.KEYWORD_MODEL_TOP_P == 0.75
    assert settings.KEYWORD_MODEL_THREADS == 3
    assert settings.KEYWORD_MODEL_GPU_LAYERS == 8
    assert settings.KEYWORD_MODEL_ENABLED is False


def test_s3_not_configured_when_bucket_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.setenv("S3_ACCESS_KEY", "access")
    monkeypatch.setenv("S3_SECRET_KEY", "secret")
    monkeypatch.setenv("S3_REGION", "ap-northeast-2")
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    settings = Settings(_env_file=None)

    assert settings.s3_configured is False


def test_log_identifier_policy_can_be_overridden(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.setenv("LOG_INCLUDE_RAW_IDENTIFIERS", "false")
    monkeypatch.setenv("LOG_EVENT_PREVIEW_MAX_LEN", "80")

    settings = Settings(_env_file=None)

    assert settings.LOG_INCLUDE_RAW_IDENTIFIERS is False
    assert settings.LOG_EVENT_PREVIEW_MAX_LEN == 80
