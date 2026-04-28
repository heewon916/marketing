import pytest

from app.core.config import Settings


@pytest.fixture
def env_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_HOST", "test_pg")
    monkeypatch.setenv("POSTGRES_PORT", "6543")
    monkeypatch.setenv("POSTGRES_DB", "testdb")
    monkeypatch.setenv("POSTGRES_USER", "tester")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("REDIS_HOST", "test_redis")
    monkeypatch.setenv("REDIS_PORT", "6380")
    monkeypatch.setenv("REDIS_PASSWORD", "rsecret")
    monkeypatch.setenv("REDIS_DB", "2")
    monkeypatch.setenv("SESSION_TTL_SECONDS", "1800")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("S3_ACCESS_KEY", "access")
    monkeypatch.setenv("S3_SECRET_KEY", "secret")
    monkeypatch.setenv("S3_BUCKET_NAME", "bucket")
    monkeypatch.setenv("S3_REGION", "ap-northeast-2")
    monkeypatch.setenv("CLOUDFRONT_DOMAIN", "cdn.example.com")


def test_settings_parses_infra_fields(env_setup: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.POSTGRES_HOST == "test_pg"
    assert settings.POSTGRES_PORT == 6543
    assert settings.REDIS_HOST == "test_redis"
    assert settings.REDIS_DB == 2
    assert settings.SESSION_TTL_SECONDS == 1800
    assert settings.DEBUG is True


def test_postgres_dsn_format(env_setup: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.postgres_dsn == (
        "postgresql+asyncpg://tester:secret@test_pg:6543/testdb"
    )


def test_redis_url_with_password(env_setup: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.redis_url == "redis://:rsecret@test_redis:6380/2"


def _set_required_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("POSTGRES_DB", "db")
    monkeypatch.setenv("POSTGRES_USER", "u")
    monkeypatch.setenv("POSTGRES_PASSWORD", "p")


def test_redis_url_without_password(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.setenv("REDIS_HOST", "h")
    monkeypatch.setenv("REDIS_PORT", "6379")
    monkeypatch.setenv("REDIS_DB", "0")
    monkeypatch.delenv("REDIS_PASSWORD", raising=False)

    settings = Settings(_env_file=None)

    assert settings.redis_url == "redis://h:6379/0"


def test_default_container_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("REDIS_HOST", raising=False)

    settings = Settings(_env_file=None)

    assert settings.POSTGRES_HOST == "project-postgres"
    assert settings.REDIS_HOST == "project-redis"


def test_s3_configured_when_required_fields_exist(env_setup: None) -> None:
    settings = Settings(_env_file=None)

    assert settings.s3_configured is True
    assert settings.CLOUDFRONT_DOMAIN == "cdn.example.com"


def test_s3_not_configured_when_bucket_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _set_required_postgres(monkeypatch)
    monkeypatch.setenv("S3_ACCESS_KEY", "access")
    monkeypatch.setenv("S3_SECRET_KEY", "secret")
    monkeypatch.setenv("S3_REGION", "ap-northeast-2")
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    settings = Settings(_env_file=None)

    assert settings.s3_configured is False
