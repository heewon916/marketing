import logging
from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.config import settings
from app.logging import build_log_extra, preview_text
from app.schemas.sessions import ProcessUtteranceRequest
from app.services.keyword_extraction import (
    KeywordExtractionService,
)
from app.services.menu_fallback import MenuKeywordFallbackService

CONTENTS_KEY_PREFIX = "contents"
STATUS_STARTED = "STARTED"
STATUS_TEXT_GENERATED = "TEXT_GENERATED"
DEFAULT_FALLBACK_GUIDE_TEXT = "사장님의 예쁜 가게를 한 번 자랑해볼까요?"
logger = logging.getLogger(__name__)

# TODO : owner_persona 동일한 레퍼런스 캡션 중 keywords 소재와 유사한 것, 날씨, 자신의 keywords 참고해 draft caption 생성하기 
def build_draft_caption(
    keywords: list[str],
    owner_persona: str,
    cloud_cover: str,
) -> tuple[str, list[str]]:
    keyword_phrase = ", ".join(keywords) if keywords else "today's highlights"
    caption = (
        f"{cloud_cover} day, {owner_persona} mood. "
        f"How about sharing {keyword_phrase} with your audience today?"
    )
    hashtags = [f"#{kw.replace(' ', '')}" for kw in keywords[:5]]
    if cloud_cover:
        hashtags.append(f"#{cloud_cover.replace(' ', '')}")
    return caption, hashtags


def build_guide_text(keywords: list[str]) -> str:
    if not keywords:
        return "Capture the store atmosphere clearly so the main subject stands out."
    keyword_phrase = ", ".join(keywords)
    return (
        f"Make sure {keyword_phrase} is clearly visible in the shot. "
        "Check the framing and subject emphasis before shooting."
    )


def resolve_caption_keywords(
    draft_keywords: list[str],
    final_keywords: list[str],
) -> list[str]:
    return final_keywords or draft_keywords


def build_text_generation_result(
    keywords: list[str],
    owner_persona: str,
    cloud_cover: str,
    fallback_source: str | None,
) -> tuple[str, list[str], str, str, str | None]:
    draft_caption, draft_hashtags = build_draft_caption(
        keywords,
        owner_persona=owner_persona,
        cloud_cover=cloud_cover,
    )
    guide_text = (
        build_guide_text(keywords)
        if keywords
        else DEFAULT_FALLBACK_GUIDE_TEXT
    )
    effective_fallback_source = fallback_source
    if not keywords and effective_fallback_source is None:
        effective_fallback_source = "default_guide"
    stored_caption = " ".join(part for part in [draft_caption, *draft_hashtags] if part)
    return (
        draft_caption,
        draft_hashtags,
        guide_text,
        stored_caption,
        effective_fallback_source,
    )


def session_key(session_id: str) -> str:
    return f"{CONTENTS_KEY_PREFIX}:{session_id}"


async def _replace_prefixed_fields(
    redis: Redis,
    key: str,
    prefix: str,
    values: list[str],
) -> None:
    existing_fields = await redis.hkeys(key)
    stale_fields = [field for field in existing_fields if field.startswith(prefix)]
    if stale_fields:
        await redis.hdel(key, *stale_fields)

    if values:
        mapping = {
            f"{prefix}{index}": value for index, value in enumerate(values, start=1)
        }
        await redis.hset(key, mapping=mapping)


async def _delete_prefixed_fields(
    redis: Redis,
    key: str,
    prefixes: list[str],
) -> None:
    existing_fields = await redis.hkeys(key)
    stale_fields = [
        field for field in existing_fields if any(field.startswith(prefix) for prefix in prefixes)
    ]
    if stale_fields:
        await redis.hdel(key, *stale_fields)


async def _delete_fields(
    redis: Redis,
    key: str,
    fields: list[str],
) -> None:
    existing_fields = await redis.hkeys(key)
    stale_fields = [field for field in fields if field in existing_fields]
    if stale_fields:
        await redis.hdel(key, *stale_fields)


async def upsert_content_session(
    redis: Redis,
    session_id: str,
    scalar_fields: dict[str, str],
    draft_keywords: list[str] | None = None,
    final_keywords: list[str] | None = None,
    drafts: list[str] | None = None,
    photos: list[str] | None = None,
    debug_fields: dict[str, str] | None = None,
) -> None:
    key = session_key(session_id)
    ttl = settings.SESSION_TTL_SECONDS
    logger.info(
        "Persisting content session to redis.",
        extra=build_log_extra(
            "redis.content_session.upsert.started",
            component="redis",
            stage="persist_redis",
            session_id=session_id,
            outcome="started",
            redis_key=key,
            scalar_field_count=len(scalar_fields),
            draft_keyword_count=len(draft_keywords or []),
            final_keyword_count=len(final_keywords or []),
            draft_count=len(drafts or []),
            photo_count=len(photos or []),
            debug_field_count=len(debug_fields or {}),
        ),
    )

    mapping = {"status": STATUS_STARTED, **scalar_fields}
    await redis.hset(key, mapping=mapping)

    if draft_keywords is not None:
        await _replace_prefixed_fields(redis, key, "draft_keyword:", draft_keywords)
    if final_keywords is not None:
        await _replace_prefixed_fields(redis, key, "final_keyword:", final_keywords)
    if draft_keywords is not None or final_keywords is not None:
        await _delete_prefixed_fields(redis, key, ["keyword:"])
    if drafts is not None:
        await _replace_prefixed_fields(redis, key, "draft:", drafts)
    if photos is not None:
        await _replace_prefixed_fields(redis, key, "photo:", photos)
    if debug_fields is not None:
        existing_fields = await redis.hkeys(key)
        stale_fields = [field for field in existing_fields if field.startswith("debug:")]
        if stale_fields:
            await redis.hdel(key, *stale_fields)
        if debug_fields:
            await redis.hset(key, mapping=debug_fields)

    await redis.expire(key, ttl)
    logger.info(
        "Persisted content session to redis.",
        extra=build_log_extra(
            "redis.content_session.upsert.completed",
            component="redis",
            stage="persist_redis",
            session_id=session_id,
            outcome="succeeded",
            redis_key=key,
            ttl_seconds=ttl,
        ),
    )


@dataclass
class ProcessUtteranceResult:
    status: str
    draft_keywords: list[str]
    weather_signals: list[str]
    final_keywords: list[str]
    draft_caption: str
    draft_hashtags: list[str]
    guide_text: str
    caption: str


async def _persist_process_utterance_started(
    redis: Redis,
    session_id: str,
    utterance: str,
) -> None:
    await upsert_content_session(
        redis,
        session_id,
        scalar_fields={
            "caption": "",
            "utterance": utterance,
        },
    )
    logger.info(
        "Stored initial process-utterance request fields in redis.",
        extra=build_log_extra(
            "session.process_utterance.redis_store_request.completed",
            component="session",
            stage="persist_redis",
            session_id=session_id,
            outcome="succeeded",
            utterance_length=len(utterance),
            initialized_field_count=2,
        ),
    )


async def _select_keyword_state(
    extraction_result,
    payload: ProcessUtteranceRequest,
    menu_fallback_service: MenuKeywordFallbackService,
    session_id: str,
) -> tuple[list[str], list[str], list[str], str | None]:
    draft_keywords = list(extraction_result.draft_keywords)
    final_keywords = list(extraction_result.final_keywords or draft_keywords)
    weather_signals = extraction_result.weather_signals
    fallback_source: str | None = None

    logger.info(
        "Keyword extraction finished.",
        extra=build_log_extra(
            "session.process_utterance.keyword_extraction.completed",
            component="session",
            stage="keyword_extraction",
            session_id=session_id,
            outcome="succeeded",
            draft_keyword_count=len(draft_keywords),
            draft_keywords_preview=", ".join(draft_keywords[:3]),
            final_keyword_count=len(final_keywords),
            final_keywords_preview=", ".join(final_keywords[:3]),
            weather_signal_count=len(weather_signals),
            weather_signals_preview=", ".join(weather_signals[:3]),
        ),
    )

    if not draft_keywords and weather_signals:
        fallback_keyword, fallback_source = await menu_fallback_service.choose_menu_keyword(
            payload.store_id,
            weather_signals,
        )
        if fallback_keyword:
            draft_keywords = [fallback_keyword]
            final_keywords = [fallback_keyword]
            logger.info(
                "Menu keyword fallback selected a menu.",
                extra=build_log_extra(
                    "session.process_utterance.menu_fallback.completed",
                    component="session",
                    stage="menu_fallback",
                    session_id=session_id,
                    outcome="succeeded",
                    fallback_source=fallback_source,
                    fallback_keyword=fallback_keyword,
                    weather_signals_preview=", ".join(weather_signals[:3]),
                ),
            )

    return draft_keywords, final_keywords, weather_signals, fallback_source


def _build_process_utterance_debug_fields(
    weather_signals: list[str],
    fallback_source: str | None,
) -> dict[str, str]:
    debug_fields = {
        f"debug:weather_signal:{index}": value
        for index, value in enumerate(weather_signals, start=1)
    }
    if fallback_source is not None:
        debug_fields["debug:fallback_source"] = fallback_source
    return debug_fields


async def _persist_process_utterance_result(
    redis: Redis,
    session_id: str,
    caption: str,
    draft_keywords: list[str],
    final_keywords: list[str],
    debug_fields: dict[str, str],
) -> None:
    await _delete_fields(
        redis,
        session_key(session_id),
        [
            "session_id",
            "store_id",
            "owner_persona",
            "weather_condition",
            "weather_temperature",
            "date",
            "expires_at",
        ],
    )
    await upsert_content_session(
        redis,
        session_id,
        scalar_fields={
            "status": STATUS_TEXT_GENERATED,
            "caption": caption,
        },
        draft_keywords=draft_keywords,
        final_keywords=final_keywords,
        debug_fields=debug_fields,
    )
    logger.info(
        "Stored process-utterance result in redis.",
        extra=build_log_extra(
            "session.process_utterance.redis_store.completed",
            component="session",
            stage="persist_redis",
            session_id=session_id,
            outcome="succeeded",
            caption_length=len(caption),
        ),
    )


async def process_utterance(
    session_id: str,
    payload: ProcessUtteranceRequest,
    redis: Redis,
    keyword_service: KeywordExtractionService,
    menu_fallback_service: MenuKeywordFallbackService,
) -> ProcessUtteranceResult:
    await _persist_process_utterance_started(redis, session_id, payload.utterance)
    logger.info(
        "Starting keyword extraction for process-utterance.",
        extra=build_log_extra(
            "session.process_utterance.keyword_extraction.started",
            component="session",
            stage="keyword_extraction",
            session_id=session_id,
            outcome="started",
            owner_persona=payload.owner_persona,
            weather_cloud_cover=payload.weather.cloud_cover,
            utterance_length=len(payload.utterance),
            utterance_preview=preview_text(
                payload.utterance,
                settings.LOG_EVENT_PREVIEW_MAX_LEN,
            )
            if settings.LOG_INCLUDE_RAW_IDENTIFIERS
            else None,
        ),
    )
    extraction_result = await keyword_service.extract_keywords(payload.utterance)
    (
        draft_keywords,
        final_keywords,
        weather_signals,
        fallback_source,
    ) = await _select_keyword_state(
        extraction_result=extraction_result,
        payload=payload,
        menu_fallback_service=menu_fallback_service,
        session_id=session_id,
    )
    caption_keywords = resolve_caption_keywords(draft_keywords, final_keywords)
    (
        draft_caption,
        draft_hashtags,
        guide_text,
        stored_caption,
        fallback_source,
    ) = build_text_generation_result(
        keywords=caption_keywords,
        owner_persona=payload.owner_persona,
        cloud_cover=payload.weather.cloud_cover,
        fallback_source=fallback_source,
    )
    debug_fields = _build_process_utterance_debug_fields(
        weather_signals=weather_signals,
        fallback_source=fallback_source,
    )
    await _persist_process_utterance_result(
        redis=redis,
        session_id=session_id,
        caption=stored_caption,
        draft_keywords=draft_keywords,
        final_keywords=final_keywords,
        debug_fields=debug_fields,
    )

    return ProcessUtteranceResult(
        status=STATUS_TEXT_GENERATED,
        draft_keywords=draft_keywords,
        weather_signals=weather_signals,
        final_keywords=final_keywords,
        draft_caption=draft_caption,
        draft_hashtags=draft_hashtags,
        guide_text=guide_text,
        caption=stored_caption,
    )
