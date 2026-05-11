from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.postgres import get_session_factory
from app.services.canonical_keyword_resolver import (
    CanonicalKeywordMatch,
    CanonicalKeywordResolverService,
)


@dataclass
class RetrievedReferenceCaption:
    caption_id: int
    caption_content: str
    score: float | None


@dataclass
class ReferenceCaptionRetrievalResult:
    references: list[RetrievedReferenceCaption] = field(default_factory=list)
    fallback_reason: str | None = None
    candidate_count: int = 0

    @property
    def captions(self) -> list[str]:
        return [reference.caption_content for reference in self.references]

    @property
    def selected_caption_ids(self) -> list[int]:
        return [reference.caption_id for reference in self.references]


class ReferenceCaptionRetrieverService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        embedder: CanonicalKeywordResolverService,
        *,
        enabled: bool = True,
        max_references: int = 2,
    ) -> None:
        self._session_factory = session_factory
        self._embedder = embedder
        self._enabled = enabled
        self._max_references = max_references

    async def preload(self) -> None:
        return None

    async def retrieve(
        self,
        *,
        owner_persona: str,
        utterance: str,
        canonical_matches: list[CanonicalKeywordMatch],
        max_references: int | None = None,
    ) -> ReferenceCaptionRetrievalResult:
        if not self._enabled:
            return ReferenceCaptionRetrievalResult(fallback_reason="rag_disabled")

        normalized_owner_persona = owner_persona.strip().lower()
        if not normalized_owner_persona:
            return ReferenceCaptionRetrievalResult(fallback_reason="owner_persona_empty")

        canonical_keyword_ids = sorted(
            {
                match.canonical_keyword_id
                for match in canonical_matches
                if match.matched and match.canonical_keyword_id is not None
            }
        )
        if not canonical_keyword_ids:
            return ReferenceCaptionRetrievalResult(
                fallback_reason="no_canonical_keyword_ids"
            )

        utterance_text = utterance.strip()
        if not utterance_text:
            return ReferenceCaptionRetrievalResult(fallback_reason="utterance_empty")

        query_embedding = (await self._embedder.embed_queries([utterance_text]))[0]
        vector_literal = self._format_vector_literal(query_embedding)

        reference_limit = max_references or self._max_references
        candidate_count = await self._count_candidates(
            owner_persona=normalized_owner_persona,
            canonical_keyword_ids=canonical_keyword_ids,
        )
        if candidate_count == 0:
            return ReferenceCaptionRetrievalResult(
                fallback_reason="no_reference_candidates",
                candidate_count=0,
            )

        references = await self._select_candidates(
            owner_persona=normalized_owner_persona,
            canonical_keyword_ids=canonical_keyword_ids,
            vector_literal=vector_literal,
            reference_limit=reference_limit,
        )
        if not references:
            return ReferenceCaptionRetrievalResult(
                fallback_reason="no_reference_candidates",
                candidate_count=candidate_count,
            )

        return ReferenceCaptionRetrievalResult(
            references=references,
            candidate_count=candidate_count,
        )

    async def _count_candidates(
        self,
        *,
        owner_persona: str,
        canonical_keyword_ids: list[int],
    ) -> int:
        query = text(
            """
            WITH candidate_captions AS (
                SELECT DISTINCT rc.id
                FROM reference AS r
                JOIN reference_captions AS rc
                    ON rc.id = r.caption_id
                JOIN reference_caption_keywords AS rck
                    ON rck.reference_caption_id = rc.id
                WHERE LOWER(r.owner_persona::text) = :owner_persona
                  AND rck.canonical_keyword_id = ANY(CAST(:canonical_keyword_ids AS bigint[]))
            )
            SELECT COUNT(*) AS candidate_count
            FROM candidate_captions
            """
        )
        row = await self._fetch_one(
            query,
            {
                "owner_persona": owner_persona,
                "canonical_keyword_ids": canonical_keyword_ids,
            },
        )
        return int(row["candidate_count"]) if row is not None else 0

    async def _select_candidates(
        self,
        *,
        owner_persona: str,
        canonical_keyword_ids: list[int],
        vector_literal: str,
        reference_limit: int,
    ) -> list[RetrievedReferenceCaption]:
        query = text(
            """
            WITH candidate_captions AS (
                SELECT DISTINCT
                    rc.id,
                    rc.caption_content,
                    rc.embedding
                FROM reference AS r
                JOIN reference_captions AS rc
                    ON rc.id = r.caption_id
                JOIN reference_caption_keywords AS rck
                    ON rck.reference_caption_id = rc.id
                WHERE LOWER(r.owner_persona::text) = :owner_persona
                  AND rck.canonical_keyword_id = ANY(CAST(:canonical_keyword_ids AS bigint[]))
            )
            SELECT
                id AS caption_id,
                caption_content,
                1 - (embedding <=> CAST(:embedding AS vector)) AS score
            FROM candidate_captions
            ORDER BY embedding <=> CAST(:embedding AS vector) ASC, id ASC
            LIMIT :reference_limit
            """
        )
        rows = await self._fetch_all(
            query,
            {
                "owner_persona": owner_persona,
                "canonical_keyword_ids": canonical_keyword_ids,
                "embedding": vector_literal,
                "reference_limit": reference_limit,
            },
        )
        return [
            RetrievedReferenceCaption(
                caption_id=int(row["caption_id"]),
                caption_content=str(row["caption_content"]),
                score=float(row["score"]) if row["score"] is not None else None,
            )
            for row in rows
        ]

    async def _fetch_one(
        self,
        query,
        params: dict[str, Any],
    ) -> dict[str, Any] | None:
        async with self._session_factory() as session:
            result = await session.execute(query, params)
            row = result.mappings().first()
        return None if row is None else dict(row)

    async def _fetch_all(
        self,
        query,
        params: dict[str, Any],
    ) -> list[dict[str, Any]]:
        async with self._session_factory() as session:
            result = await session.execute(query, params)
            return [dict(row) for row in result.mappings().all()]

    @staticmethod
    def _format_vector_literal(embedding: list[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


def build_reference_caption_retriever_service(
    embedder: CanonicalKeywordResolverService,
) -> ReferenceCaptionRetrieverService:
    return ReferenceCaptionRetrieverService(
        session_factory=get_session_factory(),
        embedder=embedder,
    )


def get_reference_caption_retriever_service(
    request: Request,
) -> ReferenceCaptionRetrieverService:
    service = getattr(request.app.state, "reference_caption_retriever_service", None)
    if service is None:
        raise RuntimeError("Reference caption retriever service is not initialized.")
    return service
