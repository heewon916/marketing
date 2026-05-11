from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from pathlib import Path
import threading

from fastapi import Request
import tensorflow as tf
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from transformers import AutoTokenizer, TFAutoModel

from app.core.config import settings
from app.db.postgres import get_session_factory
from app.logging import build_log_extra

logger = logging.getLogger(__name__)


@dataclass
class CanonicalKeywordMatch:
    draft_keyword: str
    final_keyword: str
    display_name: str | None
    score: float | None
    matched: bool


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
        self._tokenizer = None
        self._model = None
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
                or not best_match.final_keyword
            ):
                matches.append(
                    CanonicalKeywordMatch(
                        draft_keyword=draft_keyword,
                        final_keyword=draft_keyword,
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
                    final_keyword=best_match.final_keyword,
                    display_name=best_match.display_name,
                    score=best_match.score,
                    matched=best_match.matched,
                )
            )

        return CanonicalKeywordResolution(
            final_keywords=[match.final_keyword for match in matches],
            matches=matches,
        )

    async def embed_display_names(self, display_names: list[str]) -> list[list[float]]:
        if not display_names:
            return []
        if not self._enabled:
            raise RuntimeError("Canonical keyword resolver is disabled.")
        return await asyncio.to_thread(
            self._embed_texts,
            display_names,
            "passage",
        )

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
            self._model = TFAutoModel.from_pretrained(
                self._model_name,
                cache_dir=self._model_cache_dir,
                from_pt=True,
            )

    def _embed_texts(self, texts: list[str], prefix: str) -> list[list[float]]:
        self._ensure_model_loaded()
        assert self._tokenizer is not None
        assert self._model is not None

        encoded = self._tokenizer(
            [f"{prefix}: {text}" for text in texts],
            padding=True,
            truncation=True,
            return_tensors="tf",
        )
        outputs = self._model(**encoded, training=False)
        hidden_state = outputs.last_hidden_state
        attention_mask = tf.cast(encoded["attention_mask"], hidden_state.dtype)
        attention_mask = tf.expand_dims(attention_mask, axis=-1)
        pooled = tf.reduce_sum(hidden_state * attention_mask, axis=1)
        token_counts = tf.reduce_sum(attention_mask, axis=1)
        embeddings = pooled / tf.maximum(token_counts, tf.constant(1e-9, dtype=hidden_state.dtype))
        embeddings = tf.math.l2_normalize(embeddings, axis=1)
        vectors = embeddings.numpy().tolist()

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
                code,
                display_name,
                1 - (embedding <=> CAST(:embedding AS vector)) AS score
            FROM maketing.canonical_keywords
            WHERE code IS NOT NULL
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
            final_keyword=row["code"],
            display_name=row["display_name"],
            score=float(row["score"]) if row["score"] is not None else None,
            matched=bool(row["code"]),
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
                display_name=None,
                score=None,
                matched=False,
            )
            for keyword in draft_keywords
        ]
        return CanonicalKeywordResolution(
            final_keywords=[match.final_keyword for match in matches],
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
