from __future__ import annotations

import json
import logging
import random
from collections.abc import Callable, Sequence
from uuid import UUID

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.postgres import get_session_factory
from app.logging import build_log_extra

logger = logging.getLogger(__name__)


class MenuKeywordFallbackService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        chooser: Callable[[Sequence[str]], str] | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._chooser = chooser or random.choice

    async def choose_menu_keyword(
        self,
        store_id: UUID | str,
        weather_signals: list[str],
    ) -> tuple[str | None, str | None]:
        store_id_str = str(store_id)

        try:
            for signal in weather_signals:
                menu_name = await self.find_weather_tagged_menu(store_id_str, signal)
                if menu_name is not None:
                    return menu_name, "weather_tag_menu"

            menu_name = await self.find_random_menu_for_store(store_id_str)
            if menu_name is not None:
                return menu_name, "random_menu"
        except Exception as exc:
            logger.warning(
                "Menu keyword fallback lookup failed.",
                extra=build_log_extra(
                    "menu_keyword_fallback.lookup.completed",
                    component="menu_keyword_fallback",
                    stage="lookup",
                    outcome="failed",
                    error_type=exc.__class__.__name__,
                    store_id=store_id_str,
                    weather_signals_preview=", ".join(weather_signals[:3]),
                ),
                exc_info=True,
            )
            return None, None

        return None, None

    async def find_weather_tagged_menu(
        self,
        store_id: str,
        weather_signal: str,
    ) -> str | None:
        query = text(
            """
            SELECT name
            FROM menus
            WHERE store_id = :store_id
              AND weather_tags @> CAST(:weather_tag AS jsonb)
            ORDER BY name ASC
            LIMIT 1
            """
        )
        weather_tag = json.dumps([weather_signal], ensure_ascii=False)

        async with self._session_factory() as session:
            result = await session.execute(
                query,
                {
                    "store_id": store_id,
                    "weather_tag": weather_tag,
                },
            )
            return result.scalar_one_or_none()

    async def find_random_menu_for_store(self, store_id: str) -> str | None:
        query = text(
            """
            SELECT name
            FROM menus
            WHERE store_id = :store_id
            ORDER BY name ASC
            """
        )

        async with self._session_factory() as session:
            result = await session.execute(query, {"store_id": store_id})
            names = [row[0] for row in result.fetchall() if row[0]]

        if not names:
            return None
        return self._chooser(names)


def build_menu_keyword_fallback_service() -> MenuKeywordFallbackService:
    return MenuKeywordFallbackService(session_factory=get_session_factory())


def get_menu_keyword_fallback_service(request: Request) -> MenuKeywordFallbackService:
    service = getattr(request.app.state, "menu_keyword_fallback_service", None)
    if service is None:
        raise RuntimeError("Menu keyword fallback service is not initialized.")
    return service
