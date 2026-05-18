from __future__ import annotations

from difflib import SequenceMatcher
import json
from dataclasses import dataclass, field
import re
from uuid import UUID

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.postgres import get_session_factory

DEFAULT_MENU_PROMOTION_CANDIDATE_LIMIT = 8
DEFAULT_MENU_MATCH_SIMILARITY_THRESHOLD = 0.45
DEFAULT_MENU_MATCH_SCORE_GAP = 0.08

_NORMALIZE_SEARCH_PATTERN = re.compile(r"[^0-9A-Za-z가-힣]+")


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


@dataclass(frozen=True)
class MatchedMenuContext:
    menu_id: str | None = None
    menu_name: str | None = None
    menu_description: str | None = None
    matched_keyword: str | None = None
    match_source: str = "no_menu_match"
    match_score: float | None = None

    @property
    def matched(self) -> bool:
        return self.menu_id is not None and self.menu_name is not None


@dataclass(frozen=True)
class _MenuRow:
    id: str
    name: str
    description: str | None
    normalized_name: str
    normalized_description: str


class MenuPromotionContextService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        candidate_limit: int = DEFAULT_MENU_PROMOTION_CANDIDATE_LIMIT,
        similarity_threshold: float = DEFAULT_MENU_MATCH_SIMILARITY_THRESHOLD,
        similarity_score_gap: float = DEFAULT_MENU_MATCH_SCORE_GAP,
    ) -> None:
        self._session_factory = session_factory
        self._candidate_limit = candidate_limit
        self._similarity_threshold = similarity_threshold
        self._similarity_score_gap = similarity_score_gap

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

    async def match_menu(
        self,
        *,
        store_id: UUID | str,
        draft_keywords: list[str],
    ) -> MatchedMenuContext:
        normalized_keyword_pairs = [
            (keyword, self._normalize_search_text(keyword)) for keyword in draft_keywords
        ]
        normalized_keyword_pairs = [
            (raw_keyword, normalized_keyword)
            for raw_keyword, normalized_keyword in normalized_keyword_pairs
            if normalized_keyword
        ]
        normalized_keywords = [
            normalized_keyword
            for _, normalized_keyword in normalized_keyword_pairs
        ]
        if not normalized_keyword_pairs:
            return MatchedMenuContext()

        menus = await self._load_menu_rows(store_id)
        if not menus:
            return MatchedMenuContext()

        exact_name_match = self._find_exact_name_match(menus, normalized_keywords)
        if exact_name_match is not None:
            return exact_name_match

        partial_name_match = self._find_partial_name_match(menus, normalized_keywords)
        if partial_name_match is not None:
            return partial_name_match

        fuzzy_name_match = await self._find_db_fuzzy_match(
            store_id=store_id,
            normalized_keyword_pairs=normalized_keyword_pairs,
            target_field="name",
            match_source="db_fuzzy_name_match",
        )
        if fuzzy_name_match is not None:
            return fuzzy_name_match

        partial_description_match = self._find_partial_description_match(
            menus,
            normalized_keywords,
        )
        if partial_description_match is not None:
            return partial_description_match

        fuzzy_description_match = await self._find_db_fuzzy_match(
            store_id=store_id,
            normalized_keyword_pairs=normalized_keyword_pairs,
            target_field="description",
            match_source="db_fuzzy_description_match",
        )
        if fuzzy_description_match is not None:
            return fuzzy_description_match

        fallback_match = self._find_python_fuzzy_fallback(menus, normalized_keywords)
        if fallback_match is not None:
            return fallback_match

        return MatchedMenuContext()

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

    async def _load_menu_rows(self, store_id: UUID | str) -> list[_MenuRow]:
        query = text(
            """
            SELECT
                id,
                name,
                description
            FROM menus
            WHERE store_id = :store_id
              AND name IS NOT NULL
              AND BTRIM(name) <> ''
            ORDER BY name ASC
            """
        )
        async with self._session_factory() as session:
            result = await session.execute(query, {"store_id": str(store_id)})
            rows = result.mappings().all()

        menu_rows: list[_MenuRow] = []
        for row in rows:
            name = str(row["name"]).strip()
            description = (
                str(row["description"]).strip()
                if row["description"] is not None and str(row["description"]).strip()
                else None
            )
            normalized_name = self._normalize_search_text(name)
            if not normalized_name:
                continue
            menu_rows.append(
                _MenuRow(
                    id=str(row["id"]),
                    name=name,
                    description=description,
                    normalized_name=normalized_name,
                    normalized_description=self._normalize_search_text(
                        description or ""
                    ),
                )
            )
        return menu_rows

    @staticmethod
    def _normalize_search_text(value: str) -> str:
        lowered = value.strip().lower()
        return _NORMALIZE_SEARCH_PATTERN.sub("", lowered)

    def _find_exact_name_match(
        self,
        menus: list[_MenuRow],
        normalized_keywords: list[str],
    ) -> MatchedMenuContext | None:
        matches: list[tuple[_MenuRow, str]] = []
        for menu in menus:
            for keyword in normalized_keywords:
                if menu.normalized_name == keyword:
                    matches.append((menu, keyword))
        return self._pick_best_ranked_match(matches, "exact_name_match")

    def _find_partial_name_match(
        self,
        menus: list[_MenuRow],
        normalized_keywords: list[str],
    ) -> MatchedMenuContext | None:
        matches: list[tuple[_MenuRow, str]] = []
        for menu in menus:
            for keyword in normalized_keywords:
                if keyword in menu.normalized_name:
                    matches.append((menu, keyword))
        return self._pick_best_ranked_match(matches, "partial_name_match")

    def _find_partial_description_match(
        self,
        menus: list[_MenuRow],
        normalized_keywords: list[str],
    ) -> MatchedMenuContext | None:
        matches: list[tuple[_MenuRow, str]] = []
        for menu in menus:
            if not menu.normalized_description:
                continue
            for keyword in normalized_keywords:
                if keyword in menu.normalized_description:
                    matches.append((menu, keyword))
        return self._pick_best_ranked_match(matches, "partial_description_match")

    def _pick_best_ranked_match(
        self,
        matches: list[tuple[_MenuRow, str]],
        match_source: str,
    ) -> MatchedMenuContext | None:
        if not matches:
            return None

        ranked: dict[str, tuple[_MenuRow, str, int, int]] = {}
        for menu, keyword in matches:
            current = ranked.get(menu.id)
            keyword_length = len(keyword)
            keyword_hits = 1 if current is None else current[2] + 1
            best_keyword = keyword
            best_keyword_length = keyword_length
            if current is not None:
                _, existing_keyword, _, existing_length = current
                if existing_length > keyword_length:
                    best_keyword = existing_keyword
                    best_keyword_length = existing_length
            ranked[menu.id] = (menu, best_keyword, keyword_hits, best_keyword_length)

        best_menu, matched_keyword, keyword_hits, keyword_length = max(
            ranked.values(),
            key=lambda item: (
                item[2],
                item[3],
                -len(item[0].name),
                item[0].name,
            ),
        )
        return MatchedMenuContext(
            menu_id=best_menu.id,
            menu_name=best_menu.name,
            menu_description=best_menu.description,
            matched_keyword=matched_keyword,
            match_source=match_source,
            match_score=float(keyword_hits),
        )

    async def _find_db_fuzzy_match(
        self,
        *,
        store_id: UUID | str,
        normalized_keyword_pairs: list[tuple[str, str]],
        target_field: str,
        match_source: str,
    ) -> MatchedMenuContext | None:
        field_sql = "name" if target_field == "name" else "COALESCE(description, '')"
        normalized_field_sql = (
            f"regexp_replace(lower({field_sql}), '[^0-9A-Za-z가-힣]+', '', 'g')"
        )
        query = text(
            f"""
            SELECT
                id,
                name,
                description,
                similarity(
                    {normalized_field_sql},
                    :keyword
                ) AS similarity_score
            FROM menus
            WHERE store_id = :store_id
              AND name IS NOT NULL
              AND BTRIM(name) <> ''
            ORDER BY similarity_score DESC, name ASC
            LIMIT 2
            """
        )

        best_context: MatchedMenuContext | None = None
        for raw_keyword, normalized_keyword in normalized_keyword_pairs:
            try:
                async with self._session_factory() as session:
                    result = await session.execute(
                        query,
                        {
                            "store_id": str(store_id),
                            "keyword": normalized_keyword,
                        },
                    )
                    rows = result.mappings().all()
            except DBAPIError:
                return None

            context = self._build_fuzzy_match_context(
                rows=rows,
                raw_keyword=raw_keyword,
                match_source=match_source,
            )
            if context is None:
                continue
            if best_context is None or (context.match_score or 0.0) > (
                best_context.match_score or 0.0
            ):
                best_context = context
        return best_context

    def _build_fuzzy_match_context(
        self,
        *,
        rows,
        raw_keyword: str,
        match_source: str,
    ) -> MatchedMenuContext | None:
        if not rows:
            return None

        top_row = rows[0]
        top_score = float(top_row["similarity_score"] or 0.0)
        second_score = float(rows[1]["similarity_score"] or 0.0) if len(rows) > 1 else 0.0
        if top_score < self._similarity_threshold:
            return None
        if (top_score - second_score) < self._similarity_score_gap:
            return None

        return MatchedMenuContext(
            menu_id=str(top_row["id"]),
            menu_name=str(top_row["name"]).strip(),
            menu_description=(
                str(top_row["description"]).strip()
                if top_row["description"] is not None
                and str(top_row["description"]).strip()
                else None
            ),
            matched_keyword=raw_keyword,
            match_source=match_source,
            match_score=top_score,
        )

    def _find_python_fuzzy_fallback(
        self,
        menus: list[_MenuRow],
        normalized_keywords: list[str],
    ) -> MatchedMenuContext | None:
        best_row: _MenuRow | None = None
        best_keyword: str | None = None
        best_score = 0.0
        second_score = 0.0
        for menu in menus:
            for keyword in normalized_keywords:
                score = SequenceMatcher(None, keyword, menu.normalized_name).ratio()
                if score > best_score:
                    second_score = best_score
                    best_score = score
                    best_row = menu
                    best_keyword = keyword
                elif score > second_score:
                    second_score = score

        if best_row is None or best_keyword is None:
            return None
        if best_score < self._similarity_threshold:
            return None
        if (best_score - second_score) < self._similarity_score_gap:
            return None

        return MatchedMenuContext(
            menu_id=best_row.id,
            menu_name=best_row.name,
            menu_description=best_row.description,
            matched_keyword=best_keyword,
            match_source="python_fuzzy_name_fallback",
            match_score=best_score,
        )


def build_menu_promotion_context_service() -> MenuPromotionContextService:
    return MenuPromotionContextService(session_factory=get_session_factory())


def get_menu_promotion_context_service(request: Request) -> MenuPromotionContextService:
    service = getattr(request.app.state, "menu_promotion_context_service", None)
    if service is None:
        raise RuntimeError("Menu promotion context service is not initialized.")
    return service
