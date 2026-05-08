from collections.abc import Iterator

import fakeredis
import fakeredis.aioredis
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.db.redis import get_redis
from app.main import app
from app.services.canonical_keyword_resolver import (
    CanonicalKeywordMatch,
    CanonicalKeywordResolution,
)
from app.services.caption_generation import CaptionGenerationResult
from app.services.keyword_extraction import KeywordExtractionResult

class DefaultKeywordExtractionService:
    async def extract_keywords(self, utterance: str) -> KeywordExtractionResult:
        return KeywordExtractionResult(
            purpose="메뉴 홍보",
            draft_keywords=["signature menu", "cozy table"],
            final_keywords=[],
        )


class DefaultCanonicalKeywordResolverService:
    async def resolve_keywords(
        self,
        draft_keywords: list[str],
    ) -> CanonicalKeywordResolution:
        code_map = {
            "signature menu": "CANONICAL_SIGNATURE_MENU",
            "cozy table": "CANONICAL_COZY_TABLE",
        }
        matches = [
            CanonicalKeywordMatch(
                draft_keyword=keyword,
                final_keyword=code_map.get(keyword, keyword),
                display_name=keyword if keyword in code_map else None,
                score=0.99 if keyword in code_map else None,
                matched=keyword in code_map,
            )
            for keyword in draft_keywords
        ]
        return CanonicalKeywordResolution(
            final_keywords=[match.final_keyword for match in matches],
            matches=matches,
        )


class DefaultCaptionGenerationService:
    async def generate_text(
        self,
        *,
        keywords: list[str],
        owner_persona: str,
        cloud_cover: str,
        weather_tags: list[str],
    ) -> CaptionGenerationResult:
        hashtags = [f"#{keyword.replace(' ', '')}" for keyword in keywords[:3]]
        if cloud_cover:
            hashtags.append(f"#{cloud_cover.replace(' ', '')}")
        return CaptionGenerationResult(
            guide_text="사장님의 예쁜 가게를 한 번 자랑해볼까요?",
            draft_caption=(
                f"{cloud_cover} 분위기와 {owner_persona} 무드로 "
                f"{', '.join(keywords) if keywords else '오늘의 매장'}를 소개해보세요."
            ),
            draft_hashtags=hashtags or ["#today"],
        )


@pytest.fixture(scope="session")
def fake_redis_server() -> Iterator[fakeredis.FakeServer]:
    yield fakeredis.FakeServer()


@pytest.fixture(scope="session")
def fake_redis_async(
    fake_redis_server: fakeredis.FakeServer,
) -> Iterator[fakeredis.aioredis.FakeRedis]:
    yield fakeredis.aioredis.FakeRedis(server=fake_redis_server, decode_responses=True)


@pytest.fixture(scope="session")
def fake_redis_sync(
    fake_redis_server: fakeredis.FakeServer,
) -> Iterator[fakeredis.FakeStrictRedis]:
    yield fakeredis.FakeStrictRedis(server=fake_redis_server, decode_responses=True)


@pytest.fixture(autouse=True)
def reset_fake_redis(
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> Iterator[None]:
    fake_redis_sync.flushall()
    yield
    fake_redis_sync.flushall()


@pytest.fixture(scope="session")
def client(
    fake_redis_async: fakeredis.aioredis.FakeRedis,
) -> Iterator[TestClient]:
    async def _get_redis() -> fakeredis.aioredis.FakeRedis:
        return fake_redis_async

    app.dependency_overrides[get_redis] = _get_redis
    original_keyword_enabled = settings.KEYWORD_MODEL_ENABLED
    original_caption_enabled = settings.CAPTION_MODEL_ENABLED
    original_canonical_enabled = settings.CANONICAL_KEYWORD_RESOLVER_ENABLED
    original_debug = settings.DEBUG
    settings.KEYWORD_MODEL_ENABLED = False
    settings.CAPTION_MODEL_ENABLED = False
    settings.CANONICAL_KEYWORD_RESOLVER_ENABLED = False
    settings.DEBUG = False
    with TestClient(app) as test_client:
        try:
            app.state.keyword_extraction_service = DefaultKeywordExtractionService()
            app.state.caption_generation_service = DefaultCaptionGenerationService()
            app.state.canonical_keyword_resolver_service = (
                DefaultCanonicalKeywordResolverService()
            )
            yield test_client
        finally:
            settings.KEYWORD_MODEL_ENABLED = original_keyword_enabled
            settings.CAPTION_MODEL_ENABLED = original_caption_enabled
            settings.CANONICAL_KEYWORD_RESOLVER_ENABLED = original_canonical_enabled
            settings.DEBUG = original_debug
            app.dependency_overrides.clear()


@pytest.fixture
def debug_mode() -> Iterator[None]:
    original = settings.DEBUG
    settings.DEBUG = True
    yield
    settings.DEBUG = original
