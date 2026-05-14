from __future__ import annotations

import logging

from redis.asyncio import Redis

from app.core.config import settings
from app.logging import build_log_extra

CONTENTS_KEY_PREFIX = "contents"
logger = logging.getLogger(__name__)


def session_key(session_id: str) -> str:
    return f"{CONTENTS_KEY_PREFIX}:{session_id}"


class RedisSessionStore:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def replace_prefixed_fields(
        self,
        key: str,
        prefix: str,
        values: list[str],
    ) -> None:
        existing_fields = await self.redis.hkeys(key)
        stale_fields = [field for field in existing_fields if field.startswith(prefix)]
        if stale_fields:
            await self.redis.hdel(key, *stale_fields)

        if values:
            mapping = {
                f"{prefix}{index}": value for index, value in enumerate(values, start=1)
            }
            await self.redis.hset(key, mapping=mapping)

    async def delete_prefixed_fields(
        self,
        key: str,
        prefixes: list[str],
    ) -> None:
        existing_fields = await self.redis.hkeys(key)
        stale_fields = [
            field
            for field in existing_fields
            if any(field.startswith(prefix) for prefix in prefixes)
        ]
        if stale_fields:
            await self.redis.hdel(key, *stale_fields)

    async def delete_fields(
        self,
        key: str,
        fields: list[str],
    ) -> None:
        existing_fields = await self.redis.hkeys(key)
        stale_fields = [field for field in fields if field in existing_fields]
        if stale_fields:
            await self.redis.hdel(key, *stale_fields)

    async def upsert_content_session(
        self,
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

        mapping = {"status": "STARTED", **scalar_fields}
        await self.redis.hset(key, mapping=mapping)

        if draft_keywords is not None:
            await self.replace_prefixed_fields(key, "draft_keyword:", draft_keywords)
        if final_keywords is not None:
            await self.replace_prefixed_fields(key, "final_keyword:", final_keywords)
        if draft_keywords is not None or final_keywords is not None:
            await self.delete_prefixed_fields(key, ["keyword:"])
        if weather_tags is not None:
            await self.replace_prefixed_fields(key, "weather_tag:", weather_tags)
        if drafts is not None:
            await self.replace_prefixed_fields(key, "draft:", drafts)
        if photos is not None:
            await self.replace_prefixed_fields(key, "photo:", photos)
        if debug_fields is not None:
            existing_fields = await self.redis.hkeys(key)
            stale_fields = [
                field for field in existing_fields if field.startswith("debug:")
            ]
            if stale_fields:
                await self.redis.hdel(key, *stale_fields)
            if debug_fields:
                await self.redis.hset(key, mapping=debug_fields)

        await self.redis.expire(key, ttl)
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
