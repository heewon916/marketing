import asyncio
import logging

import fakeredis
import httpx
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.caption_generation import (
    CaptionGenerationRequest,
    CaptionGenerationService,
    CaptionGenerationUnavailableError,
    DEFAULT_FALLBACK_GUIDE_TEXT,
)
from app.services.canonical_keyword_resolver import (
    CanonicalKeywordMatch,
    CanonicalKeywordResolution,
)
from app.services.keyword_extraction import KeywordExtractionUnavailableError
from app.services.menu_promotion_context import (
    MenuPromotionContext,
    StoreMenuCandidate,
)
from app.services.reference_caption_retriever import (
    ReferenceCaptionRetrievalResult,
    RetrievedReferenceCaption,
)
from app.services.sessions import (
    DAILY_SHARE_PURPOSE,
    HEALTH_CHECK_FAILURE_CAPTION,
    HEALTH_CHECK_FAILURE_GUIDE_TEXT,
    MENU_PROMOTION_PURPOSE,
    resolve_caption_keywords,
    session_key,
)
from tests.utils.session_support import (
    FakeCanonicalKeywordResolverService,
    FakeCaptionGenerationService,
    FakeKeywordExtractionService,
    FakeMenuPromotionContextService,
    FakeReferenceCaptionRetrieverService,
    VALID_PAYLOAD,
    _find_reference_caption_log_record,
    _make_chat_response,
)

EXPECTED_HEALTH_CHECK_FAILURE_GUIDE_TEXT = (
    "사장님, 잠시 후 다시 시도해 주세요. "
    "지금은 가게의 분위기와 메뉴가 잘 보이도록 자유롭게 촬영해보세요."
)
EXPECTED_HEALTH_CHECK_FAILURE_CAPTION = (
    "지금은 AI 캡션 생성에 필요한 내용이 충분하지 않아 잠시 후 다시 시도해 주세요."
)
EXPECTED_DEFAULT_FALLBACK_GUIDE_TEXT = (
    "사장님, 가게의 분위기와 메뉴가 잘 보이도록 화면을 촬영해보세요."
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
    assert isinstance(body["guide_text"], str) and body["guide_text"]
    assert isinstance(body["caption"], str) and body["caption"]


def test_process_utterance_and_health_survive_when_final_edit_is_unavailable(
    client: TestClient,
) -> None:
    original_service = getattr(app.state, "final_edit_service", None)
    original_available = getattr(app.state, "final_edit_available", True)
    original_reason = getattr(app.state, "final_edit_unavailable_reason", None)
    app.state.final_edit_service = None
    app.state.final_edit_available = False
    app.state.final_edit_unavailable_reason = "FinalEditUnavailableError: OpenCV is unavailable"

    try:
        health_response = client.get("/ai/health")
        process_response = client.post(
            "/ai/sessions/sess-final-edit-unavailable/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.final_edit_service = original_service
        app.state.final_edit_available = original_available
        app.state.final_edit_unavailable_reason = original_reason

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}
    assert process_response.status_code == 200


def test_keywords_not_exposed_in_response(client: TestClient, debug_mode: None) -> None:
    response = client.post(
        "/ai/sessions/sess-1/process-utterance",
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


def test_caption_fallback_result_uses_default_guide_without_keywords() -> None:
    service = FakeCaptionGenerationService()

    fallback_result = service.build_fallback_result(
        CaptionGenerationRequest(
            purpose=DAILY_SHARE_PURPOSE,
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


def test_process_utterance_returns_fixed_caption_when_keyword_server_unhealthy(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    session_id = "sess-keyword-unhealthy"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    keyword_service = FakeKeywordExtractionService(healthy=False)
    caption_service = FakeCaptionGenerationService(healthy=True)
    app.state.keyword_extraction_service = keyword_service
    app.state.caption_generation_service = caption_service

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
    assert HEALTH_CHECK_FAILURE_GUIDE_TEXT == EXPECTED_HEALTH_CHECK_FAILURE_GUIDE_TEXT
    assert HEALTH_CHECK_FAILURE_CAPTION == EXPECTED_HEALTH_CHECK_FAILURE_CAPTION
    assert body["guide_text"] == EXPECTED_HEALTH_CHECK_FAILURE_GUIDE_TEXT
    assert body["caption"] == EXPECTED_HEALTH_CHECK_FAILURE_CAPTION
    assert keyword_service.calls == []
    assert caption_service.calls == []
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:text_generation_fallback_source"] == "health_check_fallback"
    assert saved["debug:health_check_keyword_ok"] == "false"
    assert saved["debug:health_check_caption_ok"] == "true"


def test_process_utterance_returns_fixed_caption_when_caption_server_unhealthy(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    session_id = "sess-caption-unhealthy"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    keyword_service = FakeKeywordExtractionService(healthy=True)
    caption_service = FakeCaptionGenerationService(healthy=False)
    app.state.keyword_extraction_service = keyword_service
    app.state.caption_generation_service = caption_service

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
    assert HEALTH_CHECK_FAILURE_GUIDE_TEXT == EXPECTED_HEALTH_CHECK_FAILURE_GUIDE_TEXT
    assert HEALTH_CHECK_FAILURE_CAPTION == EXPECTED_HEALTH_CHECK_FAILURE_CAPTION
    assert body["guide_text"] == EXPECTED_HEALTH_CHECK_FAILURE_GUIDE_TEXT
    assert body["caption"] == EXPECTED_HEALTH_CHECK_FAILURE_CAPTION
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:health_check_keyword_ok"] == "true"
    assert saved["debug:health_check_caption_ok"] == "false"


def test_process_utterance_runs_health_checks_in_parallel(client: TestClient) -> None:
    session_id = "sess-health-parallel"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    call_order: list[str] = []
    keyword_started = asyncio.Event()
    caption_started = asyncio.Event()

    class ParallelKeywordService(FakeKeywordExtractionService):
        async def is_healthy(self) -> bool:
            call_order.append("keyword:start")
            keyword_started.set()
            await asyncio.wait_for(caption_started.wait(), timeout=1.0)
            call_order.append("keyword:end")
            return True

    class ParallelCaptionService(FakeCaptionGenerationService):
        async def is_healthy(self) -> bool:
            call_order.append("caption:start")
            caption_started.set()
            await asyncio.wait_for(keyword_started.wait(), timeout=1.0)
            call_order.append("caption:end")
            return True

    app.state.keyword_extraction_service = ParallelKeywordService()
    app.state.caption_generation_service = ParallelCaptionService()

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.keyword_extraction_service = original_keyword_service
        app.state.caption_generation_service = original_caption_service

    assert response.status_code == 200
    assert {"keyword:start", "caption:start"} <= set(call_order)
    assert call_order.index("keyword:start") < call_order.index("caption:end")
    assert call_order.index("caption:start") < call_order.index("keyword:end")


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
    assert fake_service.fallback_calls[0]["fallback_source"] == "caption_model_fallback"
    assert fake_service.fallback_calls[0]["fallback_keywords"] == [
        "signature menu",
        "cozy table",
    ]
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:text_generation_fallback_source"] == "caption_model_fallback"
    assert saved["caption"]


def test_process_utterance_fallback_uses_draft_keywords_for_text(
    client: TestClient,
) -> None:
    session_id = "sess-caption-fallback-draft-keywords-1"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    original_canonical_service = app.state.canonical_keyword_resolver_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        purpose=MENU_PROMOTION_PURPOSE,
        draft_keywords=["draft menu", "draft notice"],
    )
    app.state.canonical_keyword_resolver_service = FakeCanonicalKeywordResolverService(
        final_keywords=["1042:final menu", "2051:final notice"],
        display_names=["final menu", "final notice"],
        matched_indexes={0, 1},
    )
    app.state.caption_generation_service = FakeCaptionGenerationService(
        error=CaptionGenerationUnavailableError("caption unavailable")
    )

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
    body = response.json()
    assert "draft menu, draft notice" in body["guide_text"]
    assert "draft menu, draft notice" in body["caption"]
    assert "final menu" not in body["guide_text"]
    assert "final notice" not in body["caption"]


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

    async def fake_is_healthy() -> bool:
        return True

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)
    monkeypatch.setattr(service, "is_healthy", fake_is_healthy)
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
    assert "Show the dish clearly." not in body["guide_text"]
    assert "Fresh soup for tonight." not in body["caption"]
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:text_generation_fallback_source"] == "caption_model_fallback"


def test_process_utterance_passes_human_readable_keywords_to_caption_request(
    client: TestClient,
) -> None:
    session_id = "sess-caption-readable-keywords-1"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    original_canonical_service = app.state.canonical_keyword_resolver_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        purpose=MENU_PROMOTION_PURPOSE,
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


def test_process_utterance_fetches_menu_candidates_for_menu_promotion(
    client: TestClient,
) -> None:
    session_id = "sess-menu-candidates-1"
    original_caption_service = app.state.caption_generation_service
    original_menu_service = app.state.menu_promotion_context_service
    fake_caption_service = FakeCaptionGenerationService()
    fake_menu_service = FakeMenuPromotionContextService(
        result=MenuPromotionContext(
            candidates=[
                StoreMenuCandidate(
                    id="menu-1",
                    name="\ud30c\uc804",
                    price=18000,
                    description="\ube44 \uc624\ub294 \ub0a0\uc5d0 \uc5b4\uc6b8\ub9ac\ub294 \ub300\ud45c \uba54\ub274",
                    weather_tags=["PRECIP_RAIN"],
                    matched_weather_tags=["PRECIP_RAIN"],
                )
            ],
            source="weather_tag_menu",
            weather_matched_count=1,
        )
    )
    app.state.caption_generation_service = fake_caption_service
    app.state.menu_promotion_context_service = fake_menu_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.caption_generation_service = original_caption_service
        app.state.menu_promotion_context_service = original_menu_service

    assert response.status_code == 200
    assert fake_menu_service.calls[0]["store_id"] == VALID_PAYLOAD["store_id"]
    assert fake_caption_service.calls[0]["menu_candidates"][0].name == "\ud30c\uc804"


def test_process_utterance_skips_menu_candidates_for_non_menu_purpose(
    client: TestClient,
) -> None:
    session_id = "sess-menu-candidates-2"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    original_menu_service = app.state.menu_promotion_context_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        purpose="other-purpose",
        draft_keywords=["notice"],
    )
    fake_caption_service = FakeCaptionGenerationService()
    fake_menu_service = FakeMenuPromotionContextService(
        result=MenuPromotionContext(
            candidates=[
                StoreMenuCandidate(
                    id="menu-1",
                    name="\ud30c\uc804",
                    price=18000,
                    description="\ube44 \uc624\ub294 \ub0a0\uc5d0 \uc5b4\uc6b8\ub9ac\ub294 \ub300\ud45c \uba54\ub274",
                    weather_tags=["PRECIP_RAIN"],
                    matched_weather_tags=["PRECIP_RAIN"],
                )
            ],
            source="weather_tag_menu",
            weather_matched_count=1,
        )
    )
    app.state.caption_generation_service = fake_caption_service
    app.state.menu_promotion_context_service = fake_menu_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.keyword_extraction_service = original_keyword_service
        app.state.caption_generation_service = original_caption_service
        app.state.menu_promotion_context_service = original_menu_service

    assert response.status_code == 200
    assert fake_menu_service.calls == []
    assert fake_caption_service.calls[0]["menu_candidates"] == []


def test_process_utterance_stores_menu_context_debug_fields(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    session_id = "sess-menu-candidates-debug-1"
    original_caption_service = app.state.caption_generation_service
    original_menu_service = app.state.menu_promotion_context_service
    fake_caption_service = FakeCaptionGenerationService()
    fake_menu_service = FakeMenuPromotionContextService(
        result=MenuPromotionContext(
            candidates=[
                StoreMenuCandidate(
                    id="menu-1",
                    name="\ud30c\uc804",
                    price=18000,
                    description="\ube44 \uc624\ub294 \ub0a0\uc5d0 \uc5b4\uc6b8\ub9ac\ub294 \ub300\ud45c \uba54\ub274",
                    weather_tags=["PRECIP_RAIN"],
                    matched_weather_tags=["PRECIP_RAIN"],
                )
            ],
            source="weather_tag_menu",
            weather_matched_count=1,
        )
    )
    app.state.caption_generation_service = fake_caption_service
    app.state.menu_promotion_context_service = fake_menu_service

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.caption_generation_service = original_caption_service
        app.state.menu_promotion_context_service = original_menu_service

    assert response.status_code == 200
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:menu_candidate_source"] == "weather_tag_menu"
    assert saved["debug:menu_candidate_count"] == "1"
    assert saved["debug:weather_matched_menu_count"] == "1"


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
                    caption_content="reference caption one",
                    score=0.91,
                ),
                RetrievedReferenceCaption(
                    caption_id=2,
                    caption_content="reference caption two",
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
        "reference caption one",
        "reference caption two",
    ]


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
    record = _find_reference_caption_log_record(caplog.records)
    assert record.reference_caption_selected_ids == "1,2"
    assert record.reference_caption_selected_count == 2
    assert record.reference_caption_selected_details == [
        {"id": 1, "score": 0.9123, "content": "reference caption body one"},
        {"id": 2, "score": 0.88, "content": "reference caption body two"},
    ]


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


def test_validation_errors_are_rejected(client: TestClient) -> None:
    empty_utterance = dict(VALID_PAYLOAD)
    empty_utterance["utterance"] = ""
    assert client.post(
        "/ai/sessions/sess-empty/process-utterance",
        json=empty_utterance,
    ).status_code == 422

    missing_owner = {k: v for k, v in VALID_PAYLOAD.items() if k != "owner_persona"}
    assert client.post(
        "/ai/sessions/sess-owner/process-utterance",
        json=missing_owner,
    ).status_code == 422

    invalid_temperature = dict(VALID_PAYLOAD)
    invalid_temperature["weather"] = dict(VALID_PAYLOAD["weather"])
    invalid_temperature["weather"]["temperature"] = "hot"
    assert client.post(
        "/ai/sessions/sess-temp/process-utterance",
        json=invalid_temperature,
    ).status_code == 422


def test_redis_payload_persisted_and_ttl_set(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
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
    assert saved["draft_keyword:1"] == "signature menu"
    assert saved["final_keyword:1"] == "1042:signature menu"
    assert saved["final_keyword:2"] == "2051:cozy table"
    assert fake_redis_sync.ttl(session_key(session_id)) > 0


def test_process_utterance_uses_default_guide_when_no_keywords(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    session_id = "sess-default-guide-1"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
        purpose=DAILY_SHARE_PURPOSE,
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
    assert DEFAULT_FALLBACK_GUIDE_TEXT == EXPECTED_DEFAULT_FALLBACK_GUIDE_TEXT
    assert body["guide_text"] == EXPECTED_DEFAULT_FALLBACK_GUIDE_TEXT
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:purpose"] == DAILY_SHARE_PURPOSE
    assert "draft_keyword:1" not in saved
    assert fake_service.fallback_calls[0]["fallback_source"] is None


def test_caption_fallback_result_falls_back_to_keywords_when_fallback_keywords_missing() -> None:
    service = CaptionGenerationService()

    fallback_result = service.build_fallback_result(
        CaptionGenerationRequest(
            purpose=DAILY_SHARE_PURPOSE,
            keywords=["readable keyword"],
            owner_persona="calm",
            weather_tags=[],
        ),
        fallback_source="caption_model_fallback",
    )

    assert "readable keyword" in fallback_result.result.guide_text
    assert "readable keyword" in fallback_result.result.draft_caption


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
