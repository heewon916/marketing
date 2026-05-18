import asyncio
from pathlib import Path

import pytest
import torch

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


def test_canonical_keyword_resolver_embed_queries_uses_query_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CanonicalKeywordResolverService(
        session_factory=None,  # type: ignore[arg-type]
        model_name="test-model",
        embedding_dim=3,
        model_cache_dir=Path("unused"),
    )
    calls: list[tuple[list[str], str]] = []

    def fake_embed(texts: list[str], prefix: str) -> list[list[float]]:
        calls.append((texts, prefix))
        return [[0.1, 0.2, 0.3] for _ in texts]

    monkeypatch.setattr(service, "_embed_texts", fake_embed)

    result = asyncio.run(service.embed_queries(["cake", "coffee"]))

    assert result == [[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]]
    assert calls == [(["cake", "coffee"], "query")]


def test_canonical_keyword_resolver_embed_passages_uses_passage_prefix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CanonicalKeywordResolverService(
        session_factory=None,  # type: ignore[arg-type]
        model_name="test-model",
        embedding_dim=3,
        model_cache_dir=Path("unused"),
    )
    calls: list[tuple[list[str], str]] = []

    def fake_embed(texts: list[str], prefix: str) -> list[list[float]]:
        calls.append((texts, prefix))
        return [[0.4, 0.5, 0.6] for _ in texts]

    monkeypatch.setattr(service, "_embed_texts", fake_embed)

    result = asyncio.run(service.embed_passages(["dessert"]))

    assert result == [[0.4, 0.5, 0.6]]
    assert calls == [(["dessert"], "passage")]


def test_canonical_keyword_resolver_embed_texts_returns_normalized_vectors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CanonicalKeywordResolverService(
        session_factory=None,  # type: ignore[arg-type]
        model_name="test-model",
        embedding_dim=3,
        model_cache_dir=Path("unused"),
    )

    class FakeTokenizer:
        def __call__(self, texts, padding, truncation, return_tensors):
            assert texts == ["query: seasonal soup", "query: evening notice"]
            assert padding is True
            assert truncation is True
            assert return_tensors == "pt"
            return {
                "attention_mask": torch.tensor(
                    [
                        [1, 1],
                        [1, 0],
                    ],
                    dtype=torch.int64,
                )
            }

    class FakeModel:
        def __call__(self, **encoded):
            del encoded
            return type(
                "FakeOutput",
                (),
                {
                    "last_hidden_state": torch.tensor(
                        [
                            [[3.0, 0.0, 0.0], [1.0, 0.0, 0.0]],
                            [[0.0, 4.0, 0.0], [9.0, 9.0, 9.0]],
                        ],
                        dtype=torch.float32,
                    )
                },
            )()

    monkeypatch.setattr(service, "_ensure_model_loaded", lambda: None)
    service._tokenizer = FakeTokenizer()
    service._model = FakeModel()

    vectors = service._embed_texts(["seasonal soup", "evening notice"], "query")

    assert vectors == [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]


def test_canonical_keyword_resolver_embed_texts_raises_on_dimension_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CanonicalKeywordResolverService(
        session_factory=None,  # type: ignore[arg-type]
        model_name="test-model",
        embedding_dim=4,
        model_cache_dir=Path("unused"),
    )

    class FakeTokenizer:
        def __call__(self, texts, padding, truncation, return_tensors):
            del texts, padding, truncation
            assert return_tensors == "pt"
            return {
                "attention_mask": torch.tensor([[1]], dtype=torch.int64),
            }

    class FakeModel:
        def __call__(self, **encoded):
            del encoded
            return type(
                "FakeOutput",
                (),
                {
                    "last_hidden_state": torch.tensor(
                        [[[1.0, 2.0, 3.0]]],
                        dtype=torch.float32,
                    )
                },
            )()

    monkeypatch.setattr(service, "_ensure_model_loaded", lambda: None)
    service._tokenizer = FakeTokenizer()
    service._model = FakeModel()

    with pytest.raises(ValueError, match="Unexpected embedding dimension"):
        service._embed_texts(["seasonal soup"], "query")
