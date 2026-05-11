from pathlib import Path

import pytest

from app.services.canonical_keyword_resolver import (
    CanonicalKeywordMatch,
    CanonicalKeywordResolverService,
)


@pytest.mark.asyncio
async def test_canonical_keyword_resolver_returns_stored_keywords_for_matches(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CanonicalKeywordResolverService(
        session_factory=None,  # type: ignore[arg-type]
        model_name="test-model",
        embedding_dim=3,
        model_cache_dir=Path("unused"),
    )
    monkeypatch.setattr(
        service,
        "_embed_texts",
        lambda texts, prefix: [[0.1, 0.2, 0.3] for _ in texts],
    )

    async def fake_find_best_match(embedding: list[float]) -> CanonicalKeywordMatch | None:
        return CanonicalKeywordMatch(
            draft_keyword="",
            canonical_keyword_id=1042,
            final_keyword="",
            display_name="ginger",
            score=0.97,
            matched=True,
        )

    monkeypatch.setattr(service, "_find_best_match", fake_find_best_match)

    resolution = await service.resolve_keywords(["seasonal soup"])

    assert resolution.final_keywords == ["1042:ginger"]
    assert resolution.match_count == 1
    assert resolution.fallback_count == 0


@pytest.mark.asyncio
async def test_canonical_keyword_resolver_falls_back_when_lookup_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CanonicalKeywordResolverService(
        session_factory=None,  # type: ignore[arg-type]
        model_name="test-model",
        embedding_dim=3,
        model_cache_dir=Path("unused"),
    )
    monkeypatch.setattr(
        service,
        "_embed_texts",
        lambda texts, prefix: [[0.1, 0.2, 0.3] for _ in texts],
    )

    async def fake_find_best_match(embedding: list[float]) -> CanonicalKeywordMatch | None:
        return None

    monkeypatch.setattr(service, "_find_best_match", fake_find_best_match)

    resolution = await service.resolve_keywords(["seasonal soup"])

    assert resolution.final_keywords == ["seasonal soup"]
    assert resolution.match_count == 0
    assert resolution.fallback_count == 1


@pytest.mark.asyncio
async def test_canonical_keyword_resolver_falls_back_when_lookup_returns_unmatched_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CanonicalKeywordResolverService(
        session_factory=None,  # type: ignore[arg-type]
        model_name="test-model",
        embedding_dim=3,
        model_cache_dir=Path("unused"),
    )
    monkeypatch.setattr(
        service,
        "_embed_texts",
        lambda texts, prefix: [[0.1, 0.2, 0.3] for _ in texts],
    )

    async def fake_find_best_match(embedding: list[float]) -> CanonicalKeywordMatch | None:
        return CanonicalKeywordMatch(
            draft_keyword="",
            canonical_keyword_id=None,
            final_keyword="",
            display_name="ginger",
            score=0.4,
            matched=False,
        )

    monkeypatch.setattr(service, "_find_best_match", fake_find_best_match)

    resolution = await service.resolve_keywords(["seasonal soup"])

    assert resolution.final_keywords == ["seasonal soup"]
    assert resolution.match_count == 0
    assert resolution.fallback_count == 1


@pytest.mark.asyncio
async def test_canonical_keyword_resolver_falls_back_when_embedding_generation_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CanonicalKeywordResolverService(
        session_factory=None,  # type: ignore[arg-type]
        model_name="test-model",
        embedding_dim=3,
        model_cache_dir=Path("unused"),
    )

    def fail_embed(texts: list[str], prefix: str) -> list[list[float]]:
        raise RuntimeError("embedding failed")

    monkeypatch.setattr(service, "_embed_texts", fail_embed)

    resolution = await service.resolve_keywords(["seasonal soup", "evening notice"])

    assert resolution.final_keywords == ["seasonal soup", "evening notice"]
    assert resolution.match_count == 0
    assert resolution.fallback_count == 2
