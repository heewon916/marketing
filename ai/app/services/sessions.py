import logging
from dataclasses import dataclass

from redis.asyncio import Redis

from app.core.config import settings
from app.schemas.sessions import ProcessUtteranceRequest
from app.services.keyword_extraction import KeywordExtractionService

CONTENTS_KEY_PREFIX = "contents"
STATUS_STARTED = "STARTED"
STATUS_TEXT_GENERATED = "TEXT_GENERATED"
logger = logging.getLogger(__name__)


def build_draft_caption(
    keywords: list[str],
    owner_persona: str,
    weather_condition: str,
) -> tuple[str, list[str]]:
    keyword_phrase = ", ".join(keywords) if keywords else "today's highlights"
    caption = (
        f"{weather_condition} day, {owner_persona} mood. "
        f"How about sharing {keyword_phrase} with your audience today?"
    )
    hashtags = [f"#{kw.replace(' ', '')}" for kw in keywords[:5]]
    if weather_condition:
        hashtags.append(f"#{weather_condition.replace(' ', '')}")
    return caption, hashtags


def build_guide_text(keywords: list[str]) -> str:
    if not keywords:
        return "Capture the store atmosphere clearly so the main subject stands out."
    keyword_phrase = ", ".join(keywords)
    return (
        f"Make sure {keyword_phrase} is clearly visible in the shot. "
        "Check the framing and subject emphasis before shooting."
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
    keywords: list[str] | None = None,
    drafts: list[str] | None = None,
    photos: list[str] | None = None,
    debug_fields: dict[str, str] | None = None,
) -> None:
    key = session_key(session_id)
    ttl = settings.SESSION_TTL_SECONDS

    mapping = {"status": STATUS_STARTED, **scalar_fields}
    await redis.hset(key, mapping=mapping)

    if keywords is not None:
        await _replace_prefixed_fields(redis, key, "keyword:", keywords)
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


@dataclass
class ProcessUtteranceResult:
    keywords: list[str]
    draft_caption: str
    draft_hashtags: list[str]
    guide_text: str


async def process_utterance(
    session_id: str,
    payload: ProcessUtteranceRequest,
    redis: Redis,
    keyword_service: KeywordExtractionService,
) -> ProcessUtteranceResult:
    logger.info(
        "Starting keyword extraction for process-utterance.",
        extra={
            "session_id": session_id,
            "owner_persona": payload.owner_persona,
            "weather_condition": payload.weather.condition,
        },
    )
    keywords = await keyword_service.extract_keywords(payload.utterance)
    logger.info(
        "Keyword extraction finished.",
        extra={
            "session_id": session_id,
            "keyword_count": len(keywords),
            "keywords_preview": ", ".join(keywords[:3]),
        },
    )
    draft_caption, draft_hashtags = build_draft_caption(
        keywords,
        owner_persona=payload.owner_persona,
        weather_condition=payload.weather.condition,
    )
    guide_text = build_guide_text(keywords)
    stored_caption = " ".join(part for part in [draft_caption, *draft_hashtags] if part)

    redis_payload = {
        "status": STATUS_TEXT_GENERATED,
        "caption": stored_caption,
    }
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
        scalar_fields=redis_payload,
        keywords=keywords,
    )
    logger.info(
        "Stored process-utterance result in redis.",
        extra={
            "session_id": session_id,
            "caption_length": len(stored_caption),
        },
    )

    return ProcessUtteranceResult(
        keywords=keywords,
        draft_caption=stored_caption,
        draft_hashtags=draft_hashtags,
        guide_text=guide_text,
    )
