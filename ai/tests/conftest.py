import asyncio
import sys
from collections.abc import Iterator

import fakeredis
import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.redis import get_redis
from app.main import app
from app.services.keyword_extraction import KeywordExtractionResult

if sys.platform == "win32" and hasattr(asyncio, "WindowsProactorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


class DefaultKeywordExtractionService:
    async def extract_keywords(self, utterance: str) -> KeywordExtractionResult:
        return KeywordExtractionResult(
            keywords=["signature menu", "cozy table"],
            weather_signals=[],
        )


@pytest.fixture
def fake_redis_server() -> Iterator[fakeredis.FakeServer]:
    yield fakeredis.FakeServer()


@pytest.fixture
def fake_redis_async(
    fake_redis_server: fakeredis.FakeServer,
) -> Iterator[fakeredis.aioredis.FakeRedis]:
    yield fakeredis.aioredis.FakeRedis(server=fake_redis_server, decode_responses=True)


@pytest.fixture
def fake_redis_sync(
    fake_redis_server: fakeredis.FakeServer,
) -> Iterator[fakeredis.FakeStrictRedis]:
    yield fakeredis.FakeStrictRedis(server=fake_redis_server, decode_responses=True)


@pytest.fixture
def client(
    fake_redis_async: fakeredis.aioredis.FakeRedis,
) -> Iterator[TestClient]:
    async def _get_redis() -> fakeredis.aioredis.FakeRedis:
        return fake_redis_async

    app.dependency_overrides[get_redis] = _get_redis
    original_keyword_enabled = settings.KEYWORD_MODEL_ENABLED
    original_debug = settings.DEBUG
    settings.KEYWORD_MODEL_ENABLED = False
    settings.DEBUG = False
    with TestClient(app) as test_client:
        try:
            app.state.keyword_extraction_service = DefaultKeywordExtractionService()
            yield test_client
        finally:
            settings.KEYWORD_MODEL_ENABLED = original_keyword_enabled
            settings.DEBUG = original_debug
            app.dependency_overrides.clear()


@pytest.fixture
def debug_mode() -> Iterator[None]:
    original = settings.DEBUG
    settings.DEBUG = True
    yield
    settings.DEBUG = original
