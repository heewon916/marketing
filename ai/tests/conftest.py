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
from app.services.caption_generation import (
    CaptionFallbackResult,
    CaptionGenerationRequest,
    CaptionGenerationResult,
    DEFAULT_FALLBACK_GUIDE_TEXT,
)
from app.services.keyword_extraction import KeywordExtractionResult
from app.services.reference_caption_retriever import (
    ReferenceCaptionRetrievalResult,
)
from app.services.menu_promotion_context import MenuPromotionContext
from app.services.weather_tags import PRECIP_CLEAR, PRECIP_CLOUDY, PRECIP_HEAVY_RAIN, PRECIP_RAIN


def _weather_context_for_tests(weather_tags: list[str]) -> str:
    if PRECIP_HEAVY_RAIN in weather_tags:
        return "폭우가 오는 날"
    if PRECIP_RAIN in weather_tags:
        return "비 오는 날"
    if PRECIP_CLEAR in weather_tags:
        return "맑은 날"
    if PRECIP_CLOUDY in weather_tags:
        return "흐린 날"
    return ""


class DefaultKeywordExtractionService:
    async def is_healthy(self) -> bool:
        return True

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
        keyword_map = {
            "signature menu": (1042, "signature menu"),
            "cozy table": (2051, "cozy table"),
        }
        matches = [
            CanonicalKeywordMatch(
                draft_keyword=keyword,
                canonical_keyword_id=(
                    keyword_map[keyword][0] if keyword in keyword_map else None
                ),
                final_keyword=(
                    f"{keyword_map[keyword][0]}:{keyword_map[keyword][1]}"
                    if keyword in keyword_map
                    else keyword
                ),
                display_name=keyword_map[keyword][1] if keyword in keyword_map else None,
                score=0.99 if keyword in keyword_map else None,
                matched=keyword in keyword_map,
            )
            for keyword in draft_keywords
        ]
        return CanonicalKeywordResolution(
            final_keywords=[match.stored_final_keyword for match in matches],
            matches=matches,
        )


class DefaultCaptionGenerationService:
    async def is_healthy(self) -> bool:
        return True

    async def generate_text(
        self,
        request: CaptionGenerationRequest,
    ) -> CaptionGenerationResult:
        weather_context = _weather_context_for_tests(request.weather_tags)
        return CaptionGenerationResult(
            guide_text="사장님의 예쁜 가게를 한 번 자랑해볼까요?",
            draft_caption=(
                f"{weather_context or '오늘의 분위기'}와 {request.owner_persona} 무드로 "
                f"{', '.join(request.keywords) if request.keywords else '오늘의 매장'}를 소개해보세요."
            ),
        )

    def build_fallback_result(
        self,
        request: CaptionGenerationRequest,
        fallback_source: str | None,
    ) -> CaptionFallbackResult:
        keyword_phrase = (
            ", ".join(request.keywords) if request.keywords else "오늘의 매장"
        )
        weather_context = _weather_context_for_tests(request.weather_tags)
        caption = (
            f"{weather_context or request.owner_persona} 분위기와 {request.owner_persona} 무드로 "
            f"{keyword_phrase}를 소개해보세요."
        )
        guide_text = (
            DEFAULT_FALLBACK_GUIDE_TEXT
            if not request.keywords
            else f"사장님, {', '.join(request.keywords)}이(가) 잘 보이도록 영상을 촬영해보세요."
        )
        effective_fallback_source = fallback_source
        if not request.keywords and effective_fallback_source is None:
            effective_fallback_source = "default_guide"
        return CaptionFallbackResult(
            result=CaptionGenerationResult(
                guide_text=guide_text,
                draft_caption=caption,
            ),
            fallback_source=effective_fallback_source,
        )


class DefaultReferenceCaptionRetrieverService:
    async def retrieve(self, **kwargs) -> ReferenceCaptionRetrievalResult:
        return ReferenceCaptionRetrievalResult()


class DefaultMenuPromotionContextService:
    async def fetch_context(self, **kwargs) -> MenuPromotionContext:
        return MenuPromotionContext()


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
            app.state.reference_caption_retriever_service = (
                DefaultReferenceCaptionRetrieverService()
            )
            app.state.menu_promotion_context_service = (
                DefaultMenuPromotionContextService()
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
