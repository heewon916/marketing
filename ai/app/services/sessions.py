import logging
from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.config import settings
from app.logging import build_log_extra, preview_text
from app.schemas.sessions import ProcessUtteranceRequest
from app.services.keyword_extraction import (
    KeywordExtractionService,
)
from app.services.caption_generation import (
    CaptionGenerationRequest,
    CaptionGenerationResult,
    CaptionGenerationService,
    CaptionGenerationUnavailableError,
)
from app.services.content_purpose import ContentPurpose
from app.services.canonical_keyword_resolver import (
    CanonicalKeywordResolverService,
    CanonicalKeywordResolution,
)
from app.services.weather_tags import evaluate_weather_tags

CONTENTS_KEY_PREFIX = "contents"
STATUS_STARTED = "STARTED"
STATUS_TEXT_GENERATED = "TEXT_GENERATED"
logger = logging.getLogger(__name__)

def resolve_caption_keywords(
    draft_keywords: list[str],
    final_keywords: list[str],
) -> list[str]:
    return final_keywords or draft_keywords


def _result_from_caption_generation(
    result: CaptionGenerationResult,
) -> tuple[str, list[str], str, str, None]:
    return (
        result.draft_caption,
        result.draft_hashtags,
        result.guide_text,
        result.stored_caption,
        None,
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
    weather_tags: list[str] | None = None,
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
            weather_tag_count=len(weather_tags or []),
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
    if weather_tags is not None:
        await _replace_prefixed_fields(redis, key, "weather_tag:", weather_tags)
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
    purpose: ContentPurpose
    weather_tags: list[str]
    draft_keywords: list[str]
    final_keywords: list[str]
    draft_caption: str
    draft_hashtags: list[str]
    guide_text: str
    caption: str


async def _persist_process_utterance_started(
    redis: Redis,
    session_id: str,
    utterance: str,
    weather_tags: list[str],
) -> None:
    await upsert_content_session(
        redis,
        session_id,
        scalar_fields={
            "caption": "",
            "utterance": utterance,
        },
        weather_tags=weather_tags,
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
            weather_tag_count=len(weather_tags),
            initialized_field_count=2,
        ),
    )


def _build_keyword_state(
    extraction_result,
    session_id: str,
) -> tuple[ContentPurpose, list[str]]:
    purpose = extraction_result.purpose
    draft_keywords = list(extraction_result.draft_keywords)

    logger.info(
        "Keyword extraction finished.",
        extra=build_log_extra(
            "session.process_utterance.keyword_extraction.completed",
            component="session",
            stage="keyword_extraction",
            session_id=session_id,
            outcome="succeeded",
            purpose=purpose,
            draft_keyword_count=len(draft_keywords),
            draft_keywords_preview=", ".join(draft_keywords[:3]),
        ),
    )

    return purpose, draft_keywords


def _build_final_keyword_state(
    draft_keywords: list[str],
    resolution: CanonicalKeywordResolution,
    session_id: str,
) -> list[str]:
    final_keywords = list(resolution.final_keywords or draft_keywords)
    logger.info(
        "Canonical keyword resolution finished.",
        extra=build_log_extra(
            "session.process_utterance.canonical_resolution.completed",
            component="session",
            stage="canonical_resolution",
            session_id=session_id,
            outcome="succeeded",
            draft_keyword_count=len(draft_keywords),
            draft_keywords_preview=", ".join(draft_keywords[:3]),
            final_keyword_count=len(final_keywords),
            final_keywords_preview=", ".join(final_keywords[:3]),
            canonical_match_count=resolution.match_count,
            canonical_fallback_count=resolution.fallback_count,
        ),
    )
    return final_keywords


def _build_process_utterance_debug_fields(
    purpose: ContentPurpose,
    canonical_resolution: CanonicalKeywordResolution,
) -> dict[str, str]:
    return {
        "debug:purpose": purpose,
        "debug:canonical_match_count": str(canonical_resolution.match_count),
        "debug:canonical_fallback_count": str(canonical_resolution.fallback_count),
    }


async def _persist_process_utterance_result(
    redis: Redis,
    session_id: str,
    caption: str,
    weather_tags: list[str],
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
        weather_tags=weather_tags,
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
    caption_service: CaptionGenerationService,
    canonical_keyword_resolver: CanonicalKeywordResolverService,
) -> ProcessUtteranceResult:
    weather_tags = evaluate_weather_tags(
        payload.weather,
        target_date=payload.date,
    )
    await _persist_process_utterance_started(
        redis,
        session_id,
        payload.utterance,
        weather_tags,
    )
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
            weather_tag_count=len(weather_tags),
            weather_tags_preview=", ".join(weather_tags[:3]),
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
    purpose, draft_keywords = _build_keyword_state(
        extraction_result=extraction_result,
        session_id=session_id,
    )
    canonical_resolution = await canonical_keyword_resolver.resolve_keywords(
        draft_keywords
    )
    final_keywords = _build_final_keyword_state(
        draft_keywords=draft_keywords,
        resolution=canonical_resolution,
        session_id=session_id,
    )
    caption_keywords = resolve_caption_keywords(draft_keywords, final_keywords)
    caption_request = CaptionGenerationRequest(
        purpose=purpose,
        keywords=caption_keywords,
        owner_persona=payload.owner_persona,
        cloud_cover=payload.weather.cloud_cover,
        weather_tags=weather_tags,
    )
    fallback_source: str | None = None
    if not caption_keywords:
        fallback_result = caption_service.build_fallback_result(
            caption_request,
            fallback_source=None,
        )
        (
            draft_caption,
            draft_hashtags,
            guide_text,
            stored_caption,
            fallback_source,
        ) = (
            fallback_result.result.draft_caption,
            fallback_result.result.draft_hashtags,
            fallback_result.result.guide_text,
            fallback_result.result.stored_caption,
            fallback_result.fallback_source,
        )
        logger.info(
            "Built text generation result from default guide fallback.",
            extra=build_log_extra(
                "session.process_utterance.text_generation.completed",
                component="session",
                stage="text_generation",
                session_id=session_id,
                outcome="fallback",
                text_generation_source="default_guide",
                purpose=purpose,
                weather_tag_count=len(weather_tags),
                weather_tags_preview=", ".join(weather_tags[:3]),
                draft_caption_length=len(draft_caption),
                guide_text_length=len(guide_text),
            ),
        )
    else:
        try:
            (
                draft_caption,
                draft_hashtags,
                guide_text,
                stored_caption,
                fallback_source,
            ) = _result_from_caption_generation(
                await caption_service.generate_text(caption_request)
            )
            logger.info(
                "Built text generation result from caption model.",
                extra=build_log_extra(
                    "session.process_utterance.text_generation.completed",
                    component="session",
                    stage="text_generation",
                    session_id=session_id,
                    outcome="succeeded",
                    text_generation_source="caption_model",
                    purpose=purpose,
                    weather_tag_count=len(weather_tags),
                    weather_tags_preview=", ".join(weather_tags[:3]),
                    draft_caption_length=len(draft_caption),
                    guide_text_length=len(guide_text),
                ),
            )
        except CaptionGenerationUnavailableError as exc:
            fallback_result = caption_service.build_fallback_result(
                caption_request,
                fallback_source="caption_model_fallback",
            )
            (
                draft_caption,
                draft_hashtags,
                guide_text,
                stored_caption,
                fallback_source,
            ) = (
                fallback_result.result.draft_caption,
                fallback_result.result.draft_hashtags,
                fallback_result.result.guide_text,
                fallback_result.result.stored_caption,
                fallback_result.fallback_source,
            )
            logger.warning(
                "Caption model generation failed; falling back to rule-based text generation: %s",
                exc,
                exc_info=True,
                extra=build_log_extra(
                    "session.process_utterance.text_generation.completed",
                    component="session",
                    stage="text_generation",
                    session_id=session_id,
                    outcome="fallback",
                    text_generation_source="rule_based_fallback",
                    error_type=exc.__class__.__name__,
                    purpose=purpose,
                    weather_tag_count=len(weather_tags),
                    weather_tags_preview=", ".join(weather_tags[:3]),
                    draft_caption_length=len(draft_caption),
                    guide_text_length=len(guide_text),
                ),
            )
    debug_fields = _build_process_utterance_debug_fields(
        purpose=purpose,
        canonical_resolution=canonical_resolution,
    )
    if fallback_source is not None:
        debug_fields["debug:text_generation_fallback_source"] = fallback_source
    await _persist_process_utterance_result(
        redis=redis,
        session_id=session_id,
        caption=stored_caption,
        weather_tags=weather_tags,
        draft_keywords=draft_keywords,
        final_keywords=final_keywords,
        debug_fields=debug_fields,
    )

    return ProcessUtteranceResult(
        status=STATUS_TEXT_GENERATED,
        purpose=purpose,
        weather_tags=weather_tags,
        draft_keywords=draft_keywords,
        final_keywords=final_keywords,
        draft_caption=draft_caption,
        draft_hashtags=draft_hashtags,
        guide_text=guide_text,
        caption=stored_caption,
    )
