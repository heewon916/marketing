import asyncio
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
from app.services.menu_promotion_context import MenuPromotionContext
from app.services.reference_caption_retriever import (
    ReferenceCaptionRetrievalResult,
)
from tests.utils.session_support import _weather_context_for_tests

if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class DefaultKeywordExtractionService:
    async def is_healthy(self) -> bool:
        return True

    async def extract_keywords(self, utterance: str) -> KeywordExtractionResult:
        return KeywordExtractionResult(
            purpose="\uba54\ub274 \ud64d\ubcf4",
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
            guide_text="\uc0ac\uc7a5\ub2d8\uc758 \uacf5\uac04 \uac00\uce58\ub97c \ub354 \ubd80\uac01\uc2dc\ud0a4\ub294 \uc601\uc0c1 \ubb38\uad6c\ub97c \ub9cc\ub4e4\uc5b4\ubcf4\uc138\uc694.",
            draft_caption=(
                f"{weather_context or '\uc624\ub298\uc758 \ubd84\uc704\uae30'}\uc5d0 {request.owner_persona} \ubb34\ub4dc\ub85c "
                f"{', '.join(request.keywords) if request.keywords else '\uc624\ub298\uc758 \ub9e4\uc7a5'}\ub97c \uc18c\uac1c\ud574\ubcf4\uc138\uc694."
            ),
        )

    def build_fallback_result(
        self,
        request: CaptionGenerationRequest,
        fallback_source: str | None,
    ) -> CaptionFallbackResult:
        keyword_phrase = (
            ", ".join(request.keywords) if request.keywords else "\uc624\ub298\uc758 \ub9e4\uc7a5"
        )
        weather_context = _weather_context_for_tests(request.weather_tags)
        caption = (
            f"{weather_context or request.owner_persona} \ubd84\uc704\uae30\uc5d0 {request.owner_persona} \ubb34\ub4dc\ub85c "
            f"{keyword_phrase}\ub97c \uc18c\uac1c\ud574\ubcf4\uc138\uc694."
        )
        guide_text = (
            DEFAULT_FALLBACK_GUIDE_TEXT
            if not request.keywords
            else f"\uc0ac\uc7a5\ub2d8, {', '.join(request.keywords)}\uc774 \ub354 \ubcf4\uc774\ub3c4\ub85d \uc601\uc0c1\uc744 \ucd2c\uc601\ud574\ubcf4\uc138\uc694."
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
