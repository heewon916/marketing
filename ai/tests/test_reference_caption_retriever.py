from collections.abc import Awaitable
from typing import Any

import pytest

from app.services.canonical_keyword_resolver import CanonicalKeywordMatch
from app.services.reference_caption_retriever import (
    ReferenceCaptionRetrieverService,
    RetrievedReferenceCaption,
)


def _run_immediate(awaitable: Awaitable[object]) -> object:
    iterator = awaitable.__await__()
    try:
        yielded = next(iterator)
    except StopIteration as exc:
        return exc.value

    while True:
        try:
            if hasattr(yielded, "__await__"):
                yielded = iterator.send(_run_immediate(yielded))
            else:
                yielded = iterator.send(None)
        except StopIteration as exc:
            return exc.value


class DummyEmbedder:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    async def embed_queries(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        return [[0.1, 0.2, 0.3]]


def _build_service(
    *,
    enabled: bool = True,
    max_references: int = 2,
) -> ReferenceCaptionRetrieverService:
    return ReferenceCaptionRetrieverService(
        session_factory=None,  # type: ignore[arg-type]
        embedder=DummyEmbedder(),  # type: ignore[arg-type]
        enabled=enabled,
        max_references=max_references,
    )


def test_reference_caption_retriever_skips_when_disabled() -> None:
    service = _build_service(enabled=False)

    result = _run_immediate(
        service.retrieve(
            owner_persona="aesthetic",
            utterance="seasonal cake",
            canonical_matches=[],
        )
    )

    assert result.references == []
    assert result.fallback_reason == "rag_disabled"


def test_reference_caption_retriever_skips_without_canonical_keyword_ids() -> None:
    service = _build_service()

    result = _run_immediate(
        service.retrieve(
            owner_persona="aesthetic",
            utterance="seasonal cake",
            canonical_matches=[
                CanonicalKeywordMatch(
                    draft_keyword="케이크",
                    canonical_keyword_id=None,
                    final_keyword="케이크",
                    display_name=None,
                    score=None,
                    matched=False,
                )
            ],
        )
    )

    assert result.references == []
    assert result.fallback_reason == "no_canonical_keyword_ids"


def test_reference_caption_retriever_returns_selected_references(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = _build_service(max_references=2)

    async def fake_count_candidates(**kwargs: Any) -> int:
        assert kwargs["owner_persona"] == "aesthetic"
        assert kwargs["canonical_keyword_ids"] == [1042, 2051]
        return 3

    async def fake_select_candidates(**kwargs: Any) -> list[RetrievedReferenceCaption]:
        assert kwargs["owner_persona"] == "aesthetic"
        assert kwargs["canonical_keyword_ids"] == [1042, 2051]
        assert kwargs["reference_limit"] == 2
        return [
            RetrievedReferenceCaption(
                caption_id=1,
                caption_content="첫 번째 레퍼런스 캡션",
                score=0.92,
            ),
            RetrievedReferenceCaption(
                caption_id=2,
                caption_content="두 번째 레퍼런스 캡션",
                score=0.88,
            ),
        ]

    monkeypatch.setattr(service, "_count_candidates", fake_count_candidates)
    monkeypatch.setattr(service, "_select_candidates", fake_select_candidates)

    result = _run_immediate(
        service.retrieve(
            owner_persona="AESTHETIC",
            utterance="seasonal cake",
            canonical_matches=[
                CanonicalKeywordMatch(
                    draft_keyword="케이크",
                    canonical_keyword_id=1042,
                    final_keyword="1042:케이크",
                    display_name="케이크",
                    score=0.99,
                    matched=True,
                ),
                CanonicalKeywordMatch(
                    draft_keyword="공지",
                    canonical_keyword_id=2051,
                    final_keyword="2051:공지",
                    display_name="공지",
                    score=0.95,
                    matched=True,
                ),
            ],
        )
    )

    assert result.candidate_count == 3
    assert result.selected_caption_ids == [1, 2]
    assert result.captions == [
        "첫 번째 레퍼런스 캡션",
        "두 번째 레퍼런스 캡션",
    ]
    assert result.fallback_reason is None
