from collections.abc import Awaitable
import asyncio
import logging
from uuid import uuid4

import fakeredis
import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.orientation.predictor import OrientationPredictor
from app.schemas.sessions import ExtractFramesResponse, FinalEditResponse
from app.services.caption_generation import (
    CaptionFallbackResult,
    CaptionGenerationRequest,
    CaptionGenerationResult,
    CaptionGenerationService,
    CaptionGenerationUnavailableError,
    DEFAULT_FALLBACK_GUIDE_TEXT,
)
from app.services.final_edit import FinalEditResult, FinalEditService
from app.services.frame_extraction import ExtractFramesResult
from app.services.canonical_keyword_resolver import (
    CanonicalKeywordMatch,
    CanonicalKeywordResolution,
)
from app.services.keyword_extraction import (
    KeywordExtractionResult,
    KeywordExtractionService,
    KeywordExtractionUnavailableError,
)
from app.services.reference_caption_retriever import (
    ReferenceCaptionRetrievalResult,
    RetrievedReferenceCaption,
)
from app.services.sessions import (
    resolve_caption_keywords,
    session_key,
)
from app.services.weather_tags import PRECIP_CLEAR, PRECIP_CLOUDY, PRECIP_HEAVY_RAIN, PRECIP_RAIN


def _weather_context_for_tests(weather_tags: list[str]) -> str:
    if PRECIP_HEAVY_RAIN in weather_tags:
        return "폭우가 오는 날"
    if PRECIP_RAIN in weather_tags:
        return "비 오는 날"
    if PRECIP_CLEAR in weather_tags:
        return "맑은 날"
    if PRECIP_CLOUDY in weather_tags:
        return "흐린 날"
    return ""




def _make_chat_response(
    status_code: int,
    *,
    content: str = "",
    url: str = "http://llama-server:8000/v1/chat/completions",
) -> httpx.Response:
    return httpx.Response(
        status_code,
        request=httpx.Request("POST", url),
        json={"choices": [{"message": {"content": content}}]},
    )

VALID_PAYLOAD = {
    "store_id": str(uuid4()),
    "utterance": "warm lighting cozy table signature menu",
    "owner_persona": "aesthetic",
    "date": "2026-04-27",
    "weather": {
        "temperature": 18.5,
        "precipitation": 0.0,
        "cloud_cover": "맑음",
        "humidity": 45,
        "wind_speed": 2.5,
        "pm10": 85,
        "pm25": 35,
        "diurnal_range": 12.0,
        "discomfort_index": 63,
        "heavy_rain_warning": None,
        "typhoon_warning": None,
    },
}

VALID_EXTRACT_PAYLOAD = {
    "session_id": str(uuid4()),
    "video": "/inputs/test-session/test-video.mp4",
}
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


class FakeFrameExtractionService:
    def __init__(self, result: ExtractFramesResult) -> None:
        self.result = result
        self.calls: list[tuple[str, str]] = []

    async def extract_and_upload(
        self,
        session_id: str,
        video_key: str,
    ) -> ExtractFramesResult:
        self.calls.append((session_id, video_key))
        return self.result


class FakeFinalEditService:
    def __init__(self, result: FinalEditResult) -> None:
        self.result = result
        self.calls: list[tuple[str, list[str]]] = []

    async def edit_and_upload(
        self,
        session_id: str,
        drafts: list[str],
    ) -> FinalEditResult:
        self.calls.append((session_id, drafts))
        return self.result


class FakeKeywordExtractionService:
    def __init__(
        self,
        purpose: str = "메뉴 홍보",
        draft_keywords: list[str] | None = None,
        final_keywords: list[str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.purpose = purpose
        self.draft_keywords = (
            draft_keywords
            if draft_keywords is not None
            else ["signature menu", "cozy table"]
        )
        self.final_keywords = final_keywords if final_keywords is not None else []
        self.error = error
        self.calls: list[str] = []

    async def extract_keywords(self, utterance: str) -> KeywordExtractionResult:
        self.calls.append(utterance)
        if self.error is not None:
            raise self.error
        return KeywordExtractionResult(
            purpose=self.purpose,
            draft_keywords=self.draft_keywords,
            final_keywords=self.final_keywords,
        )


class FakeCanonicalKeywordResolverService:
    def __init__(
        self,
        final_keywords: list[str] | None = None,
        display_names: list[str] | None = None,
        matched_indexes: set[int] | None = None,
    ) -> None:
        self.final_keywords = final_keywords
        self.display_names = display_names
        self.matched_indexes = matched_indexes
        self.calls: list[list[str]] = []

    @staticmethod
    def _parse_stored_final_keyword(value: str) -> tuple[int | None, str | None]:
        keyword_id, separator, display_name = value.partition(":")
        if not separator:
            return None, None
        try:
            return int(keyword_id), display_name or None
        except ValueError:
            return None, None

    async def resolve_keywords(
        self,
        draft_keywords: list[str],
    ) -> CanonicalKeywordResolution:
        self.calls.append(list(draft_keywords))
        final_keywords = (
            list(self.final_keywords)
            if self.final_keywords is not None
            else [f"{1000 + index}:{keyword}" for index, keyword in enumerate(draft_keywords)]
        )
        display_names = (
            list(self.display_names)
            if self.display_names is not None
            else [
                self._parse_stored_final_keyword(final_keyword)[1] or draft_keyword
                for draft_keyword, final_keyword in zip(
                    draft_keywords, final_keywords, strict=True
                )
            ]
        )
        matched_indexes = (
            set(self.matched_indexes)
            if self.matched_indexes is not None
            else set(range(len(draft_keywords)))
        )
        matches = []
        for index, draft_keyword in enumerate(draft_keywords):
            matched = index in matched_indexes
            stored_final_keyword = final_keywords[index] if matched else draft_keyword
            canonical_keyword_id, parsed_display_name = self._parse_stored_final_keyword(
                stored_final_keyword
            )
            matches.append(
                CanonicalKeywordMatch(
                    draft_keyword=draft_keyword,
                    canonical_keyword_id=canonical_keyword_id if matched else None,
                    final_keyword=stored_final_keyword,
                    display_name=(
                        display_names[index] if matched else parsed_display_name
                    )
                    if matched
                    else None,
                    score=0.99 if matched else None,
                    matched=matched,
                )
            )
        return CanonicalKeywordResolution(
            final_keywords=[match.stored_final_keyword for match in matches],
            matches=matches,
        )


class FakeCaptionGenerationService:
    def __init__(
        self,
        result: CaptionGenerationResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result or CaptionGenerationResult(
            guide_text="키워드가 잘 보이도록 구도를 잡아보세요.",
            draft_caption="오늘의 메뉴를 자연스럽게 소개해보세요.",
        )
        self.error = error
        self.calls: list[dict[str, object]] = []
        self.fallback_calls: list[dict[str, object]] = []

    async def generate_text(
        self,
        request: CaptionGenerationRequest,
    ) -> CaptionGenerationResult:
        self.calls.append(
            {
                "purpose": request.purpose,
                "keywords": list(request.keywords),
                "owner_persona": request.owner_persona,
                "weather_tags": list(request.weather_tags),
                "reference_captions": list(request.reference_captions),
            }
        )
        if self.error is not None:
            raise self.error
        return self.result

    def build_fallback_result(
        self,
        request: CaptionGenerationRequest,
        fallback_source: str | None,
    ) -> CaptionFallbackResult:
        self.fallback_calls.append(
            {
                "purpose": request.purpose,
                "keywords": list(request.keywords),
                "owner_persona": request.owner_persona,
                "weather_tags": list(request.weather_tags),
                "reference_captions": list(request.reference_captions),
                "fallback_source": fallback_source,
            }
        )
        keyword_phrase = (
            ", ".join(request.keywords) if request.keywords else "오늘의 매장"
        )
        weather_context = _weather_context_for_tests(request.weather_tags)
        caption = (
            f"{weather_context or request.owner_persona} 분위기와 {request.owner_persona} 무드로 "
            f"{keyword_phrase}를 소개해보세요."
        )
        guide_text = (
            DEFAULT_FALLBACK_GUIDE_TEXT
            if not request.keywords
            else f"사장님, {', '.join(request.keywords)}이(가) 잘 보이도록 영상을 촬영해보세요."
        )
        effective_fallback_source = fallback_source
        if not request.keywords and effective_fallback_source is None:
            effective_fallback_source = "default_guide"
        return CaptionFallbackResult(
            result=CaptionGenerationResult(
                guide_text=guide_text,
                draft_caption=caption,
            ),
            fallback_source=effective_fallback_source,
        )


class FakeReferenceCaptionRetrieverService:
    def __init__(
        self,
        result: ReferenceCaptionRetrievalResult | None = None,
        error: Exception | None = None,
    ) -> None:
        self.result = result or ReferenceCaptionRetrievalResult()
        self.error = error
        self.calls: list[dict[str, object]] = []

    async def retrieve(
        self,
        *,
        owner_persona: str,
        utterance: str,
        canonical_matches: list[CanonicalKeywordMatch],
        max_references: int | None = None,
    ) -> ReferenceCaptionRetrievalResult:
        self.calls.append(
            {
                "owner_persona": owner_persona,
                "utterance": utterance,
                "canonical_matches": list(canonical_matches),
                "max_references": max_references,
            }
        )
        if self.error is not None:
            raise self.error
        return self.result


class StubDraftDownloader:
    is_configured = True

    async def download_draft(self, draft_key: str, destination) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(draft_key.encode("utf-8"))


class StubPredictor:
    def predict_angle(self, image_path) -> float:
        return 90.0

    def correct_orientation(self, source_path, destination_path, predicted_angle):
        destination_path.write_bytes(source_path.read_bytes())
        return destination_path


class FailingUploader:
    is_configured = True

    def __init__(self) -> None:
        self.uploaded: list[str] = []
        self.deleted: list[str] = []

    async def upload_final(self, session_id: str, image_path, final_index: int) -> str:
        if final_index == 2:
            raise RuntimeError("upload_failed")
        uploaded_path = f"/ai-finals/{session_id}/final-{final_index:03d}.jpg"
        self.uploaded.append(uploaded_path)
        return uploaded_path

    async def delete_final(self, uploaded_path: str) -> None:
        self.deleted.append(uploaded_path)


def _find_reference_caption_log_record(
    caplog: pytest.LogCaptureFixture,
) -> logging.LogRecord:
    return next(
        record
        for record in caplog.records
        if getattr(record, "event", None)
        == "session.process_utterance.reference_caption_retrieval.completed"
    )


def test_process_utterance_returns_session_id_and_guide(client: TestClient) -> None:
    session_id = "redis-session-id-123"

    response = client.post(
        f"/ai/sessions/{session_id}/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["status"] == "TEXT_GENERATED"
    assert isinstance(body["guide_text"], str)
    assert len(body["guide_text"]) > 0
    assert isinstance(body["caption"], str)
    assert len(body["caption"]) > 0


def test_keywords_not_exposed_in_response(client: TestClient) -> None:
    response = client.post(
        "/ai/sessions/sess-1/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200
    body = response.json()
    assert "keywords" not in body
    assert "draft_keywords" not in body
    assert "final_keywords" not in body


def test_keywords_not_exposed_even_when_debug_on(
    client: TestClient, debug_mode: None
) -> None:
    response = client.post(
        "/ai/sessions/sess-2/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200
    body = response.json()
    assert "keywords" not in body
    assert "draft_keywords" not in body
    assert "final_keywords" not in body


def test_resolve_caption_keywords_prefers_display_names() -> None:
    resolution = CanonicalKeywordResolution(
        final_keywords=["1042:signature menu", "draft notice"],
        matches=[
            CanonicalKeywordMatch(
                draft_keyword="draft menu",
                canonical_keyword_id=1042,
                final_keyword="1042:signature menu",
                display_name="signature menu",
                score=0.99,
                matched=True,
            ),
            CanonicalKeywordMatch(
                draft_keyword="draft notice",
                canonical_keyword_id=None,
                final_keyword="draft notice",
                display_name=None,
                score=None,
                matched=False,
            ),
        ],
    )

    assert resolve_caption_keywords(["draft menu", "draft notice"], resolution) == [
        "signature menu",
        "draft notice",
    ]


def test_resolve_caption_keywords_falls_back_to_draft_keywords_without_matches() -> None:
    resolution = CanonicalKeywordResolution(final_keywords=[], matches=[])

    assert resolve_caption_keywords(["draft menu"], resolution) == ["draft menu"]


def test_caption_fallback_result_uses_default_guide_without_keywords() -> None:
    service = FakeCaptionGenerationService()

    fallback_result = service.build_fallback_result(
        CaptionGenerationRequest(
            purpose="일상 공유",
            keywords=[],
            owner_persona="calm",
            weather_tags=[],
        ),
        fallback_source=None,
    )

    assert fallback_result.result.draft_caption
    assert fallback_result.result.guide_text == DEFAULT_FALLBACK_GUIDE_TEXT
    assert fallback_result.result.stored_caption == fallback_result.result.draft_caption
    assert fallback_result.fallback_source == "default_guide"


def test_process_utterance_returns_503_when_keyword_extraction_fails(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    session_id = "sess-keyword-fail"
    original_service = app.state.keyword_extraction_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        error=KeywordExtractionUnavailableError("model unavailable")
    )

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.keyword_extraction_service = original_service

    assert response.status_code == 503
    assert response.json()["detail"] == "Keyword extraction is unavailable."
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["status"] == "STARTED"
    assert saved["utterance"] == VALID_PAYLOAD["utterance"]
    assert saved["caption"] == ""


def test_process_utterance_falls_back_when_caption_generation_fails(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    session_id = "sess-caption-fallback"
    original_service = app.state.caption_generation_service
    fake_service = FakeCaptionGenerationService(
        error=CaptionGenerationUnavailableError("caption unavailable")
    )
    app.state.caption_generation_service = fake_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.caption_generation_service = original_service

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["guide_text"], str)
    assert isinstance(body["caption"], str)
    assert fake_service.fallback_calls[0]["purpose"] == "메뉴 홍보"
    assert fake_service.fallback_calls[0]["fallback_source"] == "caption_model_fallback"
    assert "cloud_cover" not in fake_service.fallback_calls[0]
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:text_generation_fallback_source"] == "caption_model_fallback"
    assert saved["caption"]


def test_process_utterance_falls_back_to_korean_when_caption_model_returns_english(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session_id = "sess-caption-english-fallback"
    original_service = app.state.caption_generation_service
    service = CaptionGenerationService(base_url="http://caption-server:8002")

    async def fake_post_chat_completion(
        prompt: str,
        *,
        include_response_format: bool,
        strict_language: bool,
    ):
        return _make_chat_response(
            200,
            content=(
                '{"guide_text":"Show the dish clearly.",'
                '"caption":"Fresh soup for tonight."}'
            ),
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)
    app.state.caption_generation_service = service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.caption_generation_service = original_service

    assert response.status_code == 200
    body = response.json()
    assert "사장님" in body["guide_text"]
    assert "Make sure" not in body["guide_text"]
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:text_generation_fallback_source"] == "caption_model_fallback"
    assert "Make sure" not in saved["caption"]


def test_process_utterance_passes_purpose_to_caption_request(
    client: TestClient,
) -> None:
    session_id = "sess-purpose-forward-1"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        purpose="영업 공지",
        draft_keywords=["임시 휴무"],
    )
    fake_service = FakeCaptionGenerationService()
    app.state.caption_generation_service = fake_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.keyword_extraction_service = original_keyword_service
        app.state.caption_generation_service = original_caption_service

    assert response.status_code == 200
    assert fake_service.calls[0]["purpose"] == "영업 공지"
    assert "cloud_cover" not in fake_service.calls[0]


def test_process_utterance_passes_human_readable_keywords_to_caption_request(
    client: TestClient,
) -> None:
    session_id = "sess-caption-readable-keywords-1"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    original_canonical_service = app.state.canonical_keyword_resolver_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        purpose="메뉴 홍보",
        draft_keywords=["signature menu", "evening notice"],
    )
    app.state.canonical_keyword_resolver_service = FakeCanonicalKeywordResolverService(
        final_keywords=["1042:signature menu", "2051:evening notice"],
        display_names=["signature menu", "evening notice"],
        matched_indexes={0, 1},
    )
    fake_service = FakeCaptionGenerationService()
    app.state.caption_generation_service = fake_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.keyword_extraction_service = original_keyword_service
        app.state.caption_generation_service = original_caption_service
        app.state.canonical_keyword_resolver_service = original_canonical_service

    assert response.status_code == 200
    assert fake_service.calls[0]["keywords"] == ["signature menu", "evening notice"]


def test_process_utterance_passes_reference_captions_to_caption_request(
    client: TestClient,
) -> None:
    session_id = "sess-caption-reference-captions-1"
    original_caption_service = app.state.caption_generation_service
    original_retriever_service = app.state.reference_caption_retriever_service
    fake_caption_service = FakeCaptionGenerationService()
    fake_retriever_service = FakeReferenceCaptionRetrieverService(
        result=ReferenceCaptionRetrievalResult(
            references=[
                RetrievedReferenceCaption(
                    caption_id=1,
                    caption_content="첫 번째 레퍼런스 캡션",
                    score=0.91,
                ),
                RetrievedReferenceCaption(
                    caption_id=2,
                    caption_content="두 번째 레퍼런스 캡션",
                    score=0.88,
                ),
            ],
            candidate_count=2,
        )
    )
    app.state.caption_generation_service = fake_caption_service
    app.state.reference_caption_retriever_service = fake_retriever_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.caption_generation_service = original_caption_service
        app.state.reference_caption_retriever_service = original_retriever_service

    assert response.status_code == 200
    assert fake_caption_service.calls[0]["reference_captions"] == [
        "첫 번째 레퍼런스 캡션",
        "두 번째 레퍼런스 캡션",
    ]
    assert fake_retriever_service.calls[0]["owner_persona"] == VALID_PAYLOAD["owner_persona"]


def test_process_utterance_logs_selected_reference_caption_details(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    session_id = "sess-caption-reference-captions-log-1"
    original_retriever_service = app.state.reference_caption_retriever_service
    fake_retriever_service = FakeReferenceCaptionRetrieverService(
        result=ReferenceCaptionRetrievalResult(
            references=[
                RetrievedReferenceCaption(
                    caption_id=1,
                    caption_content="reference caption body one",
                    score=0.91234,
                ),
                RetrievedReferenceCaption(
                    caption_id=2,
                    caption_content="reference caption body two",
                    score=0.88,
                ),
            ],
            candidate_count=2,
        )
    )
    app.state.reference_caption_retriever_service = fake_retriever_service
    app_logger = logging.getLogger("app")
    app_logger.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger="app")

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app_logger.removeHandler(caplog.handler)
        app.state.reference_caption_retriever_service = original_retriever_service

    assert response.status_code == 200
    record = _find_reference_caption_log_record(caplog)
    assert record.reference_caption_selected_ids == "1,2"
    assert record.reference_caption_selected_count == 2
    assert record.reference_caption_selected_details == [
        {
            "id": 1,
            "score": 0.9123,
            "content": "reference caption body one",
        },
        {
            "id": 2,
            "score": 0.88,
            "content": "reference caption body two",
        },
    ]


def test_process_utterance_skips_reference_captions_when_retriever_returns_no_matches(
    client: TestClient,
) -> None:
    session_id = "sess-caption-reference-captions-2"
    original_caption_service = app.state.caption_generation_service
    original_retriever_service = app.state.reference_caption_retriever_service
    fake_caption_service = FakeCaptionGenerationService()
    fake_retriever_service = FakeReferenceCaptionRetrieverService(
        result=ReferenceCaptionRetrievalResult(
            references=[],
            fallback_reason="no_reference_candidates",
            candidate_count=0,
        )
    )
    app.state.caption_generation_service = fake_caption_service
    app.state.reference_caption_retriever_service = fake_retriever_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.caption_generation_service = original_caption_service
        app.state.reference_caption_retriever_service = original_retriever_service

    assert response.status_code == 200
    assert fake_caption_service.calls[0]["reference_captions"] == []


def test_process_utterance_omits_reference_caption_details_when_no_matches(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    session_id = "sess-caption-reference-captions-log-2"
    original_retriever_service = app.state.reference_caption_retriever_service
    fake_retriever_service = FakeReferenceCaptionRetrieverService(
        result=ReferenceCaptionRetrievalResult(
            references=[],
            fallback_reason="no_reference_candidates",
            candidate_count=0,
        )
    )
    app.state.reference_caption_retriever_service = fake_retriever_service
    app_logger = logging.getLogger("app")
    app_logger.addHandler(caplog.handler)
    caplog.set_level(logging.INFO, logger="app")

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app_logger.removeHandler(caplog.handler)
        app.state.reference_caption_retriever_service = original_retriever_service

    assert response.status_code == 200
    record = _find_reference_caption_log_record(caplog)
    assert record.reference_caption_candidate_count == 0
    assert record.reference_caption_fallback_reason == "no_reference_candidates"
    assert not hasattr(record, "reference_caption_selected_details")


def test_process_utterance_skips_reference_captions_when_retriever_fails(
    client: TestClient,
) -> None:
    session_id = "sess-caption-reference-captions-3"
    original_caption_service = app.state.caption_generation_service
    original_retriever_service = app.state.reference_caption_retriever_service
    fake_caption_service = FakeCaptionGenerationService()
    fake_retriever_service = FakeReferenceCaptionRetrieverService(
        error=RuntimeError("retriever unavailable")
    )
    app.state.caption_generation_service = fake_caption_service
    app.state.reference_caption_retriever_service = fake_retriever_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.caption_generation_service = original_caption_service
        app.state.reference_caption_retriever_service = original_retriever_service

    assert response.status_code == 200
    assert fake_caption_service.calls[0]["reference_captions"] == []


def test_process_utterance_omits_reference_caption_details_when_retriever_fails(
    client: TestClient,
    caplog: pytest.LogCaptureFixture,
) -> None:
    session_id = "sess-caption-reference-captions-log-3"
    original_retriever_service = app.state.reference_caption_retriever_service
    fake_retriever_service = FakeReferenceCaptionRetrieverService(
        error=RuntimeError("retriever unavailable")
    )
    app.state.reference_caption_retriever_service = fake_retriever_service
    app_logger = logging.getLogger("app")
    app_logger.addHandler(caplog.handler)
    caplog.set_level(logging.WARNING, logger="app")

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app_logger.removeHandler(caplog.handler)
        app.state.reference_caption_retriever_service = original_retriever_service

    assert response.status_code == 200
    record = _find_reference_caption_log_record(caplog)
    assert record.outcome == "failed"
    assert record.error_type == "RuntimeError"
    assert not hasattr(record, "reference_caption_selected_details")


def test_empty_utterance_rejected(client: TestClient) -> None:
    payload = dict(VALID_PAYLOAD)
    payload["utterance"] = ""

    response = client.post(
        "/ai/sessions/sess-3/process-utterance",
        json=payload,
    )

    assert response.status_code == 422


def test_missing_owner_persona_rejected(client: TestClient) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "owner_persona"}

    response = client.post(
        "/ai/sessions/sess-4/process-utterance",
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_temperature_rejected(client: TestClient) -> None:
    payload = dict(VALID_PAYLOAD)
    payload["weather"] = dict(VALID_PAYLOAD["weather"])
    payload["weather"]["temperature"] = "hot"

    response = client.post(
        "/ai/sessions/sess-5/process-utterance",
        json=payload,
    )

    assert response.status_code == 422


def test_missing_cloud_cover_rejected(client: TestClient) -> None:
    payload = dict(VALID_PAYLOAD)
    payload["weather"] = dict(VALID_PAYLOAD["weather"])
    payload["weather"].pop("cloud_cover")

    response = client.post(
        "/ai/sessions/sess-5b/process-utterance",
        json=payload,
    )

    assert response.status_code == 422


def test_redis_payload_persisted(
    client: TestClient, fake_redis_sync: fakeredis.FakeStrictRedis
) -> None:
    session_id = "sess-redis-1"

    response = client.post(
        f"/ai/sessions/{session_id}/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200

    saved = fake_redis_sync.hgetall(session_key(session_id))

    assert saved["status"] == "TEXT_GENERATED"
    assert saved["utterance"] == VALID_PAYLOAD["utterance"]
    assert saved["caption"]
    assert "맑은 날" in saved["caption"]
    assert "CANONICAL_" not in saved["caption"]
    draft_keyword_fields = [
        field for field in saved if field.startswith("draft_keyword:")
    ]
    final_keyword_fields = [
        field for field in saved if field.startswith("final_keyword:")
    ]
    assert 1 <= len(draft_keyword_fields) <= 3
    assert len(draft_keyword_fields) == len(final_keyword_fields)
    assert saved["draft_keyword:1"] == "signature menu"
    assert saved["final_keyword:1"] == "1042:signature menu"
    assert saved["final_keyword:2"] == "2051:cozy table"
    weather_tag_fields = [
        field for field in saved if field.startswith("weather_tag:")
    ]
    assert weather_tag_fields == [
        "weather_tag:1",
        "weather_tag:2",
        "weather_tag:3",
        "weather_tag:4",
    ]
    assert saved["weather_tag:1"] == "PRECIP_CLEAR"
    assert saved["weather_tag:2"] == "TEMP_MILD"
    assert saved["weather_tag:3"] == "SPECIAL_FINE_DUST"
    assert saved["weather_tag:4"] == "SPECIAL_SEASONAL_CHANGE"
    assert "session_id" not in saved
    assert "store_id" not in saved
    assert "owner_persona" not in saved
    assert "weather_condition" not in saved
    assert "weather_temperature" not in saved
    assert "date" not in saved
    assert "expires_at" not in saved


def test_purpose_persisted_in_debug_fields(
    client: TestClient, fake_redis_sync: fakeredis.FakeStrictRedis
) -> None:
    session_id = "sess-purpose-1"
    original_service = app.state.keyword_extraction_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        purpose="영업 공지",
        draft_keywords=["임시 휴무", "정상영업"],
    )

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.keyword_extraction_service = original_service

    assert response.status_code == 200

    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:purpose"] == "영업 공지"
    assert saved["debug:canonical_match_count"] == "0"
    assert saved["debug:canonical_fallback_count"] == "2"


def test_process_utterance_uses_default_guide_when_no_keywords(
    client: TestClient, fake_redis_sync: fakeredis.FakeStrictRedis
) -> None:
    session_id = "sess-default-guide-1"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        purpose="일상 공유",
        draft_keywords=[],
    )
    fake_service = FakeCaptionGenerationService()
    app.state.caption_generation_service = fake_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.keyword_extraction_service = original_keyword_service
        app.state.caption_generation_service = original_caption_service

    assert response.status_code == 200
    body = response.json()
    assert body["guide_text"] == DEFAULT_FALLBACK_GUIDE_TEXT
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:purpose"] == "일상 공유"
    assert saved["debug:canonical_match_count"] == "0"
    assert saved["debug:canonical_fallback_count"] == "0"
    assert "draft_keyword:1" not in saved
    assert "final_keyword:1" not in saved
    assert fake_service.fallback_calls[0]["purpose"] == "일상 공유"
    assert fake_service.fallback_calls[0]["fallback_source"] is None
    assert "cloud_cover" not in fake_service.fallback_calls[0]


def test_process_utterance_falls_back_to_draft_keywords_when_canonical_lookup_misses(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    session_id = "sess-canonical-fallback-1"
    original_keyword_service = app.state.keyword_extraction_service
    original_canonical_service = app.state.canonical_keyword_resolver_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        draft_keywords=["seasonal soup", "evening notice"],
    )
    app.state.canonical_keyword_resolver_service = (
        FakeCanonicalKeywordResolverService(matched_indexes=set())
    )

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.keyword_extraction_service = original_keyword_service
        app.state.canonical_keyword_resolver_service = original_canonical_service

    assert response.status_code == 200
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["draft_keyword:1"] == "seasonal soup"
    assert saved["final_keyword:1"] == "seasonal soup"
    assert saved["final_keyword:2"] == "evening notice"
    assert saved["debug:canonical_match_count"] == "0"
    assert saved["debug:canonical_fallback_count"] == "2"


def test_redis_ttl_set(
    client: TestClient, fake_redis_sync: fakeredis.FakeStrictRedis
) -> None:
    session_id = "sess-ttl-1"

    response = client.post(
        f"/ai/sessions/{session_id}/process-utterance",
        json=VALID_PAYLOAD,
    )
    assert response.status_code == 200

    ttl = fake_redis_sync.ttl(session_key(session_id))
    assert ttl > 0


def test_extract_frames_returns_success_and_persists_result(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    original_service = app.state.frame_extraction_service
    session_id = str(uuid4())
    fake_service = FakeFrameExtractionService(
        ExtractFramesResult(
            status="FRAME_EXTRACTED",
            drafts=["/ai-drafts/session-123/draft-001.jpg"],
        )
    )
    app.state.frame_extraction_service = fake_service
    payload = {"session_id": session_id, "video": "/inputs/test-session/test-video.mp4"}

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/extract-frames",
            json=payload,
        )
    finally:
        app.state.frame_extraction_service = original_service

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["status"] == "FRAME_EXTRACTED"
    assert body["drafts"] == ["/ai-drafts/session-123/draft-001.jpg"]
    assert fake_service.calls == [(session_id, payload["video"])]

    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["status"] == "FRAME_EXTRACTED"
    assert saved["draft:1"] == "/ai-drafts/session-123/draft-001.jpg"
    assert saved["video"] == payload["video"]


def test_extract_frames_preserves_existing_final_keywords(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    original_service = app.state.frame_extraction_service
    session_id = str(uuid4())
    fake_service = FakeFrameExtractionService(
        ExtractFramesResult(
            status="FRAME_EXTRACTED",
            drafts=["/ai-drafts/session-123/draft-001.jpg"],
        )
    )
    app.state.frame_extraction_service = fake_service

    try:
        process_response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
        assert process_response.status_code == 200

        extract_response = client.post(
            f"/ai/sessions/{session_id}/extract-frames",
            json={"session_id": session_id, "video": "/inputs/test-session/test-video.mp4"},
        )
    finally:
        app.state.frame_extraction_service = original_service

    assert extract_response.status_code == 200
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["final_keyword:1"] == "1042:signature menu"
    assert saved["final_keyword:2"] == "2051:cozy table"


def test_extract_frames_returns_fail_when_service_fails(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    original_service = app.state.frame_extraction_service
    session_id = str(uuid4())
    fake_service = FakeFrameExtractionService(
        ExtractFramesResult(
            status="TEXT_GENERATED",
            drafts=[],
            failure_reason="s3_upload_unavailable",
        )
    )
    app.state.frame_extraction_service = fake_service
    payload = {"session_id": session_id, "video": "/inputs/test-session/test-video.mp4"}

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/extract-frames",
            json=payload,
        )
    finally:
        app.state.frame_extraction_service = original_service

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "TEXT_GENERATED"
    assert body["drafts"] == []

    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["status"] == "TEXT_GENERATED"
    assert "draft:1" not in saved
    assert saved["video"] == payload["video"]


def test_extract_frames_rejects_mismatched_session_id(client: TestClient) -> None:
    payload = dict(VALID_EXTRACT_PAYLOAD)
    payload["session_id"] = str(uuid4())

    response = client.post("/ai/sessions/extract-session-3/extract-frames", json=payload)

    assert response.status_code == 422


def test_extract_frames_response_limits_drafts_to_three() -> None:
    with pytest.raises(ValidationError):
        ExtractFramesResponse(
            session_id="sess",
            status="FRAME_EXTRACTED",
            drafts=["1", "2", "3", "4"],
        )


def test_final_edit_returns_success_and_persists_result(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    original_service = app.state.final_edit_service
    session_id = str(uuid4())
    drafts = [
        "/ai-drafts/session-123/draft-001.jpg",
        "/ai-drafts/session-123/draft-002.jpg",
    ]
    fake_service = FakeFinalEditService(
        FinalEditResult(
            status="PHOTO_EDITED",
            results=[
                "/ai-finals/session-123/final-001.jpg",
                "/ai-finals/session-123/final-002.jpg",
            ],
        )
    )
    app.state.final_edit_service = fake_service
    payload = {"session_id": session_id, "drafts": drafts}

    try:
        response = client.post(f"/ai/sessions/{session_id}/final-edit", json=payload)
    finally:
        app.state.final_edit_service = original_service

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["status"] == "PHOTO_EDITED"
    assert body["results"] == [
        "/ai-finals/session-123/final-001.jpg",
        "/ai-finals/session-123/final-002.jpg",
    ]
    assert fake_service.calls == [(session_id, drafts)]

    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["status"] == "PHOTO_EDITED"
    assert saved["photo:1"] == "/ai-finals/session-123/final-001.jpg"
    assert saved["photo:2"] == "/ai-finals/session-123/final-002.jpg"


def test_final_edit_preserves_existing_final_keywords(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    original_service = app.state.final_edit_service
    session_id = str(uuid4())
    fake_service = FakeFinalEditService(
        FinalEditResult(
            status="PHOTO_EDITED",
            results=["/ai-finals/session-123/final-001.jpg"],
        )
    )
    app.state.final_edit_service = fake_service

    try:
        process_response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
        assert process_response.status_code == 200

        edit_response = client.post(
            f"/ai/sessions/{session_id}/final-edit",
            json={
                "session_id": session_id,
                "drafts": ["/ai-drafts/session-123/draft-001.jpg"],
            },
        )
    finally:
        app.state.final_edit_service = original_service

    assert edit_response.status_code == 200
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["final_keyword:1"] == "1042:signature menu"
    assert saved["final_keyword:2"] == "2051:cozy table"


def test_final_edit_returns_fail_and_clears_photo_results(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    original_service = app.state.final_edit_service
    session_id = str(uuid4())
    fake_service = FakeFinalEditService(
        FinalEditResult(
            status="FRAME_EXTRACTED",
            results=[],
            failure_reason="orientation_model_load_failed",
        )
    )
    app.state.final_edit_service = fake_service
    payload = {
        "session_id": session_id,
        "drafts": ["/ai-drafts/session-123/draft-001.jpg"],
    }

    try:
        response = client.post(f"/ai/sessions/{session_id}/final-edit", json=payload)
    finally:
        app.state.final_edit_service = original_service

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FRAME_EXTRACTED"
    assert body["results"] == []

    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["status"] == "FRAME_EXTRACTED"
    assert "photo:1" not in saved


def test_final_edit_rejects_mismatched_session_id(client: TestClient) -> None:
    payload = {
        "session_id": str(uuid4()),
        "drafts": ["/ai-drafts/session-123/draft-001.jpg"],
    }

    response = client.post("/ai/sessions/edit-session-3/final-edit", json=payload)

    assert response.status_code == 422


def test_final_edit_response_limits_results_to_three() -> None:
    with pytest.raises(ValidationError):
        FinalEditResponse(
            session_id="sess",
            status="PHOTO_EDITED",
            results=["1", "2", "3", "4"],
        )


def test_final_edit_service_rolls_back_uploaded_results(tmp_path) -> None:
    uploader = FailingUploader()
    service = FinalEditService(
        predictor=StubPredictor(),
        downloader=StubDraftDownloader(),
        uploader=uploader,
        temp_root=tmp_path,
    )
    session_id = "session-rollback-1"

    result = asyncio.run(
        service.edit_and_upload(
            session_id=session_id,
            drafts=[
                "/ai-drafts/session-rollback-1/draft-001.jpg",
                "/ai-drafts/session-rollback-1/draft-002.jpg",
            ],
        )
    )

    assert result.status == "FRAME_EXTRACTED"
    assert result.results == []
    assert uploader.uploaded == ["/ai-finals/session-rollback-1/final-001.jpg"]
    assert uploader.deleted == ["/ai-finals/session-rollback-1/final-001.jpg"]
    assert not (tmp_path / session_id).exists()


def test_frame_extraction_singletons_initialized_on_app_state(
    client: TestClient,
) -> None:
    assert app.state.frame_extractor_config is not None
    assert app.state.best_frame_extractor is not None
    assert app.state.frame_extraction_service is not None
    assert app.state.frame_extraction_service.extractor is app.state.best_frame_extractor
    assert app.state.final_edit_service is not None
    assert app.state.final_edit_service.predictor.weights_path is not None
    assert app.state.keyword_extraction_service is not None
    assert app.state.caption_generation_service is not None
    assert app.state.canonical_keyword_resolver_service is not None


def test_orientation_predictor_retries_without_safetensors_on_safe_open_error() -> None:
    predictor = OrientationPredictor()
    calls: list[tuple[str, dict[str, object]]] = []

    class FakeTFAutoModel:
        @staticmethod
        def from_pretrained(model_id: str, **kwargs):
            calls.append((model_id, kwargs))
            if len(calls) == 1:
                raise TypeError("'builtins.safe_open' object is not iterable")
            return "vit-model"

    model = predictor._load_vit_base_model(FakeTFAutoModel)

    assert model == "vit-model"
    assert calls == [
        ("google/vit-base-patch16-224", {}),
        ("google/vit-base-patch16-224", {"use_safetensors": False}),
    ]


def test_keyword_extraction_service_normalizes_and_limits_keywords() -> None:
    service = KeywordExtractionService()

    keywords = service._parse_keywords(
        "["
        '"\\ub9c9\\uac78\\ub9ac", '
        '" \\ud30c\\uc804 ", '
        '"\\ub9c9\\uac78\\ub9ac", '
        '"\\uc624\\ub298", '
        '"\\ucc3b\\uc794", '
        '"\\ub514\\uc800\\ud2b8"'
        "]"
    )

    assert keywords == ["\ub9c9\uac78\ub9ac", "\ud30c\uc804", "\ucc3b\uc794"]


def test_keyword_extraction_service_strips_particles_from_keywords() -> None:
    service = KeywordExtractionService()

    assert service._normalize_keyword("\ubc24\ud638\ubc15\uc774") == "\ubc24\ud638\ubc15"
    assert (
        service._normalize_keyword("\uc81c\ucca0 \uc74c\uc2dd\uc740")
        == "\uc81c\ucca0 \uc74c\uc2dd"
    )
    assert (
        service._normalize_keyword("\ub538\uae30 \ub77c\ub5bc\ub791")
        == "\ub538\uae30 \ub77c\ub5bc"
    )


def test_keyword_extraction_service_rejects_sentence_like_keywords() -> None:
    service = KeywordExtractionService()

    assert service._normalize_keyword("\uba39\uace0 \uc0b4\uc544\uc57c\uc9c0") == ""
    assert service._normalize_keyword("\uc81c\ucca0\uc774\uc57c") == ""


def test_keyword_extraction_service_falls_back_without_morph_analyzer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService()
    monkeypatch.setattr(service, "_get_morph_analyzer", lambda: None)

    assert service._normalize_keyword("\ubc24\ud638\ubc15\uc774") == "\ubc24\ud638\ubc15"


def test_keyword_extraction_service_parses_purpose_and_keywords() -> None:
    service = KeywordExtractionService()

    result = service._parse_extraction_result(
        "{"
        '"purpose": "\uba54\ub274 \ud64d\ubcf4", '
        '"keywords": ['
        '"\\ubc24\\ud638\\ubc15", '
        '"\\uc81c\\ucca0 \\uc74c\\uc2dd", '
        '"\\ub9e4\\uc7a5"'
        "]"
        "}"
    )

    assert result.purpose == "\uba54\ub274 \ud64d\ubcf4"
    assert result.draft_keywords == ["\ubc24\ud638\ubc15", "\uc81c\ucca0 \uc74c\uc2dd"]
    assert result.final_keywords == []


def test_keyword_extraction_service_rejects_invalid_purpose() -> None:
    service = KeywordExtractionService()

    with pytest.raises(
        KeywordExtractionUnavailableError,
        match="invalid purpose",
    ):
        service._parse_extraction_result(
            '{'
            '"purpose": "\\uae30\\ud0c0", '
            '"keywords": ["\\ub9c9\\uac78\\ub9ac"]'
            "}"
        )


def test_keyword_extraction_service_rejects_empty_normalized_keywords() -> None:
    service = KeywordExtractionService()

    with pytest.raises(
        KeywordExtractionUnavailableError,
        match="no usable draft_keywords",
    ):
        service._parse_extraction_result(
            '{'
            '"purpose": "\\uc77c\\uc0c1 \\uacf5\\uc720", '
            '"keywords": ["\\uba39\\uace0 \\uc0b4\\uc544\\uc57c\\uc9c0"]'
            "}"
        )


def test_keyword_extraction_service_accepts_keyword_object_payload() -> None:
    service = KeywordExtractionService()

    result = service._parse_extraction_result(
        '{'
        '"purpose": "\\uba54\\ub274 \\ud64d\\ubcf4", '
        '"keywords": ['
        '"\\ub9c9\\uac78\\ub9ac", '
        '"\\ud30c\\uc804", '
        '"\\ub9e4\\uc7a5"'
        "]"
        "}"
    )

    assert result.purpose == "\uba54\ub274 \ud64d\ubcf4"
    assert result.draft_keywords == ["\ub9c9\uac78\ub9ac", "\ud30c\uc804"]
    assert result.final_keywords == []


def test_keyword_extraction_service_rejects_non_json_output() -> None:
    service = KeywordExtractionService()

    with pytest.raises(KeywordExtractionUnavailableError):
        service._parse_keywords("\ub9c9\uac78\ub9ac, \ud30c\uc804")


def test_keyword_extraction_service_raises_when_disabled() -> None:
    service = KeywordExtractionService(enabled=False)

    with pytest.raises(KeywordExtractionUnavailableError):
        _run_immediate(
            service.extract_keywords(
                "\uc624\ub298 \ub9c9\uac78\ub9ac\ub791 \ud30c\uc804\uc774 \ub531\uc774\ub2e4"
            )
        )


def test_keyword_extraction_service_calls_remote_server_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(
        base_url="http://llama-server:8000",
    )
    calls: list[bool] = []

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        calls.append(include_response_format)
        return _make_chat_response(
            200,
            content='{"purpose":"\\uba54\\ub274 \\ud64d\\ubcf4","keywords":["\\ub9c9\\uac78\\ub9ac"]}',
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    result = _run_immediate(
        service.extract_keywords(
            "\uc624\ub298 \ube44\uc640\uc11c \ub9c9\uac78\ub9ac\uac00 \ub561\uae34\ub2e4"
        )
    )

    assert calls == [True]
    assert result.purpose == "\uba54\ub274 \ud64d\ubcf4"
    assert result.draft_keywords == ["\ub9c9\uac78\ub9ac"]


def test_keyword_extraction_service_retries_without_response_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(
        base_url="http://llama-server:8000",
    )
    calls: list[bool] = []

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        calls.append(include_response_format)
        if include_response_format:
            return httpx.Response(
                400,
                request=httpx.Request(
                    "POST",
                    "http://llama-server:8000/v1/chat/completions",
                ),
                text="response_format is unsupported",
            )
        return _make_chat_response(
            200,
            content='{"purpose":"\\uba54\\ub274 \\ud64d\\ubcf4","keywords":["\\ud30c\\uc804"]}',
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    result = _run_immediate(
        service.extract_keywords(
            "\uc624\ub298\uc740 \ud30c\uc804\uc774 \uc798 \ub098\uac08 \uac83 \uac19\ub2e4"
        )
    )

    assert calls == [True, False]
    assert result.purpose == "\uba54\ub274 \ud64d\ubcf4"
    assert result.draft_keywords == ["\ud30c\uc804"]


def test_keyword_extraction_service_raises_on_remote_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(
        base_url="http://llama-server:8000",
    )

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    with pytest.raises(KeywordExtractionUnavailableError, match="timed out"):
        _run_immediate(
            service.extract_keywords(
                "\uc624\ub298 \ub9c9\uac78\ub9ac\uac00 \ub561\uae34\ub2e4"
            )
        )


def test_keyword_extraction_service_raises_on_remote_http_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(
        base_url="http://llama-server:8000",
    )

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        return httpx.Response(
            503,
            request=httpx.Request(
                "POST",
                "http://llama-server:8000/v1/chat/completions",
            ),
            text="server unavailable",
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    with pytest.raises(KeywordExtractionUnavailableError, match="HTTP 503"):
        _run_immediate(
            service.extract_keywords(
                "\uc624\ub298 \ud30c\uc804\uc774 \ub561\uae34\ub2e4"
            )
        )


def test_keyword_extraction_service_preload_raises_when_server_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(
        base_url="http://llama-server:8000",
    )

    class FailingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr("app.services.keyword_extraction.httpx.AsyncClient", FailingAsyncClient)

    with pytest.raises(
        KeywordExtractionUnavailableError,
        match="connectivity check failed",
    ):
        _run_immediate(service.preload())


def test_keyword_extraction_service_preload_uses_health_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(
        base_url="http://llama-server:8000",
        health_endpoint="/health",
    )
    calls: list[str] = []

    class RecordingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str) -> httpx.Response:
            calls.append(url)
            return httpx.Response(
                200,
                request=httpx.Request("GET", url),
                text="ok",
            )

    monkeypatch.setattr(
        "app.services.keyword_extraction.httpx.AsyncClient",
        RecordingAsyncClient,
    )

    _run_immediate(service.preload())

    assert calls == ["http://llama-server:8000/health"]


def test_keyword_extraction_service_preload_raises_on_http_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(
        base_url="http://llama-server:8000",
        health_endpoint="/health",
    )

    class FailingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str) -> httpx.Response:
            return httpx.Response(
                404,
                request=httpx.Request("GET", url),
                text="not found",
            )

    monkeypatch.setattr(
        "app.services.keyword_extraction.httpx.AsyncClient",
        FailingAsyncClient,
    )

    with pytest.raises(
        KeywordExtractionUnavailableError,
        match="HTTP 404",
    ):
        _run_immediate(service.preload())
