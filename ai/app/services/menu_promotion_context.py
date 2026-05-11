from __future__ import annotations

import json
from dataclasses import dataclass, field
from uuid import UUID

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.postgres import get_session_factory

DEFAULT_MENU_PROMOTION_CANDIDATE_LIMIT = 8


@dataclass(frozen=True)
class StoreMenuCandidate:
    id: str
    name: str
    price: int | None
    description: str | None
    weather_tags: list[str] = field(default_factory=list)
    matched_weather_tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MenuPromotionContext:
    candidates: list[StoreMenuCandidate] = field(default_factory=list)
    source: str = "no_menu_candidates"
    weather_matched_count: int = 0


class MenuPromotionContextService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        candidate_limit: int = DEFAULT_MENU_PROMOTION_CANDIDATE_LIMIT,
    ) -> None:
        self._session_factory = session_factory
        self._candidate_limit = candidate_limit

    async def preload(self) -> None:
        query = text("SELECT 1")
        async with self._session_factory() as session:
            await session.execute(query)

    async def fetch_context(
        self,
        *,
        store_id: UUID | str,
        weather_tags: list[str],
    ) -> MenuPromotionContext:
        query = text(
            """
            SELECT
                id,
                name,
                price,
                description,
                weather_tags
            FROM menus
            WHERE store_id = :store_id
            ORDER BY
                CASE
                    WHEN description IS NULL OR BTRIM(description) = '' THEN 1
                    ELSE 0
                END ASC,
                name ASC
            """
        )

        async with self._session_factory() as session:
            result = await session.execute(query, {"store_id": str(store_id)})
            rows = result.mappings().all()

        all_candidates = [
            self._build_candidate(row, weather_tags) for row in rows if row["name"]
        ]
        if not all_candidates:
            return MenuPromotionContext()

        matched_candidates = [
            candidate for candidate in all_candidates if candidate.matched_weather_tags
        ]
        if matched_candidates:
            return MenuPromotionContext(
                candidates=matched_candidates[: self._candidate_limit],
                source="weather_tag_menu",
                weather_matched_count=len(matched_candidates),
            )

        return MenuPromotionContext(
            candidates=all_candidates[: self._candidate_limit],
            source="store_menu_fallback",
            weather_matched_count=0,
        )

    def _build_candidate(
        self,
        row,
        weather_tags: list[str],
    ) -> StoreMenuCandidate:
        menu_weather_tags = self._parse_weather_tags(row["weather_tags"])
        matched_weather_tags = [
            tag for tag in weather_tags if tag in set(menu_weather_tags)
        ]
        return StoreMenuCandidate(
            id=str(row["id"]),
            name=str(row["name"]),
            price=int(row["price"]) if row["price"] is not None else None,
            description=(
                str(row["description"]).strip()
                if row["description"] is not None and str(row["description"]).strip()
                else None
            ),
            weather_tags=menu_weather_tags,
            matched_weather_tags=matched_weather_tags,
        )

    @staticmethod
    def _parse_weather_tags(value: object) -> list[str]:
        if value is None:
            return []
        if isinstance(value, list):
            return [str(tag) for tag in value if str(tag).strip()]
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
            except json.JSONDecodeError:
                return []
            if isinstance(parsed, list):
                return [str(tag) for tag in parsed if str(tag).strip()]
        return []


def build_menu_promotion_context_service() -> MenuPromotionContextService:
    return MenuPromotionContextService(session_factory=get_session_factory())


def get_menu_promotion_context_service(request: Request) -> MenuPromotionContextService:
    service = getattr(request.app.state, "menu_promotion_context_service", None)
    if service is None:
        raise RuntimeError("Menu promotion context service is not initialized.")
    return service
