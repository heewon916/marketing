from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from pathlib import Path
import threading
from typing import Any

from fastapi import Request
import torch
import torch.nn.functional as F
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from transformers import AutoModel, AutoTokenizer

from app.core.config import settings
from app.db.postgres import get_session_factory
from app.logging import build_log_extra

logger = logging.getLogger(__name__)


@dataclass
class CanonicalKeywordMatch:
    draft_keyword: str
    canonical_keyword_id: int | None
    final_keyword: str
    display_name: str | None
    score: float | None
    matched: bool

    @property
    def stored_final_keyword(self) -> str:
        if self.matched and self.canonical_keyword_id is not None and self.display_name:
            return f"{self.canonical_keyword_id}:{self.display_name}"
        return self.draft_keyword


@dataclass
class CanonicalKeywordResolution:
    final_keywords: list[str]
    matches: list[CanonicalKeywordMatch]

    @property
    def match_count(self) -> int:
        return sum(1 for match in self.matches if match.matched)

    @property
    def fallback_count(self) -> int:
        return sum(1 for match in self.matches if not match.matched)


class CanonicalKeywordResolverService:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        model_name: str,
        embedding_dim: int,
        model_cache_dir: Path | None = None,
        enabled: bool = True,
    ) -> None:
        self._session_factory = session_factory
        self._model_name = model_name
        self._embedding_dim = embedding_dim
        self._model_cache_dir = str(model_cache_dir) if model_cache_dir else None
        self._enabled = enabled
        self._tokenizer: Any | None = None
        self._model: Any | None = None
        self._lock = threading.Lock()

    async def preload(self) -> None:
        if not self._enabled:
            return
        await asyncio.to_thread(self._ensure_model_loaded)

    async def resolve_keywords(
        self,
        draft_keywords: list[str],
    ) -> CanonicalKeywordResolution:
        if not draft_keywords:
            return CanonicalKeywordResolution(final_keywords=[], matches=[])
        if not self._enabled:
            return self._build_fallback_resolution(draft_keywords)

        try:
            embeddings = await asyncio.to_thread(
                self._embed_texts,
                draft_keywords,
                "query",
            )
        except Exception as exc:
            logger.warning(
                "Canonical keyword embeddings could not be generated. Falling back to draft keywords.",
                exc_info=True,
                extra=build_log_extra(
                    "canonical_keyword.embedding.failed",
                    component="canonical_keyword_resolver",
                    stage="embedding",
                    outcome="failed",
                    error_type=exc.__class__.__name__,
                    draft_keyword_count=len(draft_keywords),
                ),
            )
            return self._build_fallback_resolution(draft_keywords)

        matches: list[CanonicalKeywordMatch] = []
        for draft_keyword, embedding in zip(draft_keywords, embeddings, strict=True):
            try:
                best_match = await self._find_best_match(embedding)
            except Exception as exc:
                logger.warning(
                    "Canonical keyword lookup failed. Falling back to draft keyword.",
                    exc_info=True,
                    extra=build_log_extra(
                        "canonical_keyword.lookup.failed",
                        component="canonical_keyword_resolver",
                        stage="lookup",
                        outcome="failed",
                        error_type=exc.__class__.__name__,
                        draft_keyword=draft_keyword,
                    ),
                )
                best_match = None

            if (
                best_match is None
                or not best_match.matched
                or best_match.canonical_keyword_id is None
                or not best_match.display_name
            ):
                matches.append(
                    CanonicalKeywordMatch(
                        draft_keyword=draft_keyword,
                        final_keyword=draft_keyword,
                        canonical_keyword_id=None,
                        display_name=(
                            None if best_match is None else best_match.display_name
                        ),
                        score=None if best_match is None else best_match.score,
                        matched=False,
                    )
                )
                continue

            matches.append(
                CanonicalKeywordMatch(
                    draft_keyword=draft_keyword,
                    canonical_keyword_id=best_match.canonical_keyword_id,
                    final_keyword=best_match.stored_final_keyword,
                    display_name=best_match.display_name,
                    score=best_match.score,
                    matched=best_match.matched,
                )
            )

        return CanonicalKeywordResolution(
            final_keywords=[match.stored_final_keyword for match in matches],
            matches=matches,
        )

    async def embed_queries(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._enabled:
            raise RuntimeError("Canonical keyword resolver is disabled.")
        return await asyncio.to_thread(
            self._embed_texts,
            texts,
            "query",
        )

    async def embed_passages(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if not self._enabled:
            raise RuntimeError("Canonical keyword resolver is disabled.")
        return await asyncio.to_thread(
            self._embed_texts,
            texts,
            "passage",
        )

    async def embed_display_names(self, display_names: list[str]) -> list[list[float]]:
        if not display_names:
            return []
        if not self._enabled:
            raise RuntimeError("Canonical keyword resolver is disabled.")
        return await self.embed_passages(display_names)

    def _ensure_model_loaded(self) -> None:
        if self._tokenizer is not None and self._model is not None:
            return

        with self._lock:
            if self._tokenizer is not None and self._model is not None:
                return
            self._tokenizer = AutoTokenizer.from_pretrained(
                self._model_name,
                cache_dir=self._model_cache_dir,
            )
            self._model = AutoModel.from_pretrained(
                self._model_name,
                cache_dir=self._model_cache_dir,
            )
            self._model.eval()

    def _embed_texts(self, texts: list[str], prefix: str) -> list[list[float]]:
        self._ensure_model_loaded()
        assert self._tokenizer is not None
        assert self._model is not None

        encoded = self._tokenizer(
            [f"{prefix}: {text}" for text in texts],
            padding=True,
            truncation=True,
            return_tensors="pt",
        )
        with torch.inference_mode():
            outputs = self._model(**encoded)
            hidden_state = outputs.last_hidden_state
            attention_mask = encoded["attention_mask"].unsqueeze(-1).to(
                hidden_state.dtype
            )
            pooled = torch.sum(hidden_state * attention_mask, dim=1)
            token_counts = torch.sum(attention_mask, dim=1).clamp(min=1e-9)
            embeddings = pooled / token_counts
            embeddings = F.normalize(embeddings, p=2, dim=1)
        vectors = embeddings.cpu().tolist()

        for vector in vectors:
            if len(vector) != self._embedding_dim:
                raise ValueError(
                    f"Unexpected embedding dimension: expected {self._embedding_dim}, got {len(vector)}"
                )
        return vectors

    async def _find_best_match(self, embedding: list[float]) -> CanonicalKeywordMatch | None:
        vector_literal = self._format_vector_literal(embedding)
        query = text(
            """
            SELECT
                id,
                display_name,
                1 - (embedding <=> CAST(:embedding AS vector)) AS score
            FROM canonical_keywords
            ORDER BY embedding <=> CAST(:embedding AS vector) ASC
            LIMIT 1
            """
        )

        async with self._session_factory() as session:
            result = await session.execute(query, {"embedding": vector_literal})
            row = result.mappings().first()

        if row is None:
            return None

        return CanonicalKeywordMatch(
            draft_keyword="",
            canonical_keyword_id=int(row["id"]) if row["id"] is not None else None,
            final_keyword="",
            display_name=row["display_name"],
            score=float(row["score"]) if row["score"] is not None else None,
            matched=bool(row["id"]) and bool(row["display_name"]),
        )

    @staticmethod
    def _format_vector_literal(embedding: list[float]) -> str:
        return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"

    @staticmethod
    def _build_fallback_resolution(
        draft_keywords: list[str],
    ) -> CanonicalKeywordResolution:
        matches = [
            CanonicalKeywordMatch(
                draft_keyword=keyword,
                final_keyword=keyword,
                canonical_keyword_id=None,
                display_name=None,
                score=None,
                matched=False,
            )
            for keyword in draft_keywords
        ]
        return CanonicalKeywordResolution(
            final_keywords=[match.stored_final_keyword for match in matches],
            matches=matches,
        )


def build_canonical_keyword_resolver_service() -> CanonicalKeywordResolverService:
    return CanonicalKeywordResolverService(
        session_factory=get_session_factory(),
        model_name=settings.CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME,
        embedding_dim=settings.CANONICAL_KEYWORD_EMBEDDING_DIM,
        model_cache_dir=settings.CANONICAL_KEYWORD_EMBEDDING_MODEL_CACHE_DIR,
        enabled=settings.CANONICAL_KEYWORD_RESOLVER_ENABLED,
    )


def get_canonical_keyword_resolver_service(
    request: Request,
) -> CanonicalKeywordResolverService:
    service = getattr(request.app.state, "canonical_keyword_resolver_service", None)
    if service is None:
        raise RuntimeError("Canonical keyword resolver service is not initialized.")
    return service
