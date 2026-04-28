import pytest

from app.core.config import Settings


@pytest.fixture
def env_setup(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_POSTGRES_HOST", "test_pg")
    monkeypatch.setenv("AI_POSTGRES_PORT", "6543")
    monkeypatch.setenv("AI_POSTGRES_DB", "testdb")
    monkeypatch.setenv("AI_POSTGRES_USER", "tester")
    monkeypatch.setenv("AI_POSTGRES_PASSWORD", "secret")
    monkeypatch.setenv("AI_REDIS_HOST", "test_redis")
    monkeypatch.setenv("AI_REDIS_PORT", "6380")
    monkeypatch.setenv("AI_REDIS_PASSWORD", "rsecret")
    monkeypatch.setenv("AI_REDIS_DB", "2")
    monkeypatch.setenv("AI_SESSION_TTL_SECONDS", "1800")
    monkeypatch.setenv("AI_DEBUG", "true")


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


def test_redis_url_without_password(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AI_REDIS_HOST", "h")
    monkeypatch.setenv("AI_REDIS_PORT", "6379")
    monkeypatch.setenv("AI_REDIS_DB", "0")
    monkeypatch.delenv("AI_REDIS_PASSWORD", raising=False)

    settings = Settings(_env_file=None)

    assert settings.redis_url == "redis://h:6379/0"


def test_default_container_hosts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AI_POSTGRES_HOST", raising=False)
    monkeypatch.delenv("AI_REDIS_HOST", raising=False)

    settings = Settings(_env_file=None)

    assert settings.POSTGRES_HOST == "maketing_postgres"
    assert settings.REDIS_HOST == "maketing_redis"
