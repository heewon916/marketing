import asyncio

import fakeredis
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.caption_generation import (
    CaptionGenerationRequest,
    CaptionGenerationService,
    CaptionGenerationUnavailableError,
    DEFAULT_FALLBACK_GUIDE_TEXT,
)
from app.services.keyword_extraction import KeywordExtractionUnavailableError
from app.services.menu_promotion_context import MatchedMenuContext
from app.services.sessions import (
    HEALTH_CHECK_FAILURE_CAPTION,
    HEALTH_CHECK_FAILURE_GUIDE_TEXT,
    MENU_PROMOTION_PURPOSE,
    session_key,
)
from tests.utils.session_support import (
    FakeCaptionGenerationService,
    FakeKeywordExtractionService,
    FakeMenuPromotionContextService,
    VALID_PAYLOAD,
    _make_chat_response,
)

EXPECTED_HEALTH_CHECK_FAILURE_GUIDE_TEXT = (
    "사장님, 잠시 후 다시 시도해 주세요. "
    "지금은 가게의 분위기와 메뉴가 잘 보이도록 자유롭게 촬영해보세요."
)
EXPECTED_HEALTH_CHECK_FAILURE_CAPTION = (
    "지금은 AI 캡션 생성에 필요한 내용이 충분하지 않아 잠시 후 다시 시도해 주세요."
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
    assert fake_service.fallback_calls[0]["draft_keywords"] == [
        "signature menu",
        "cozy table",
    ]
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:text_generation_fallback_source"] == "caption_model_fallback"
    assert saved["caption"]


def test_process_utterance_passes_single_menu_context_to_caption_request(
    client: TestClient,
) -> None:
    session_id = "sess-menu-context-1"
    original_caption_service = app.state.caption_generation_service
    original_menu_service = app.state.menu_promotion_context_service
    fake_caption_service = FakeCaptionGenerationService()
    fake_menu_service = FakeMenuPromotionContextService(
        result=MatchedMenuContext(
            menu_id="menu-1",
            menu_name="에그 타르트",
            menu_description="겹겹이 결이 살아 있는 바삭한 디저트",
            matched_keyword="에그타르트",
            match_source="exact_name_match",
            match_score=1.0,
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
    assert fake_menu_service.calls[0]["draft_keywords"] == [
        "signature menu",
        "cozy table",
    ]
    assert fake_caption_service.calls[0]["menu_name"] == "에그 타르트"
    assert fake_caption_service.calls[0]["menu_description"] == "겹겹이 결이 살아 있는 바삭한 디저트"
    assert fake_caption_service.calls[0]["matched_keyword"] == "에그타르트"
    assert fake_caption_service.calls[0]["today"] == VALID_PAYLOAD["date"]


def test_process_utterance_stores_menu_match_debug_fields(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    session_id = "sess-menu-debug-1"
    original_menu_service = app.state.menu_promotion_context_service
    app.state.menu_promotion_context_service = FakeMenuPromotionContextService(
        result=MatchedMenuContext(
            menu_id="menu-1",
            menu_name="에그 타르트",
            menu_description="겹겹이 결이 살아 있는 바삭한 디저트",
            matched_keyword="에그타르트",
            match_source="db_fuzzy_name_match",
            match_score=0.81,
        )
    )

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/process-utterance",
            json=VALID_PAYLOAD,
        )
    finally:
        app.state.menu_promotion_context_service = original_menu_service

    assert response.status_code == 200
    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["debug:menu_match_source"] == "db_fuzzy_name_match"
    assert saved["debug:menu_candidate_count"] == "1"
    assert saved["debug:matched_keyword"] == "에그타르트"
    assert saved["debug:matched_menu_name"] == "에그 타르트"


def test_redis_payload_persisted_and_final_keywords_match_draft_keywords(
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
    assert saved["owner_persona"] == VALID_PAYLOAD["owner_persona"]
    assert saved["utterance"] == VALID_PAYLOAD["utterance"]
    assert saved["caption"]
    assert saved["draft_keyword:1"] == "signature menu"
    assert saved["final_keyword:1"] == "signature menu"
    assert saved["final_keyword:2"] == "cozy table"
    assert fake_redis_sync.ttl(session_key(session_id)) > 0


def test_process_utterance_uses_default_guide_when_no_keywords(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    session_id = "sess-default-guide-1"
    original_keyword_service = app.state.keyword_extraction_service
    original_caption_service = app.state.caption_generation_service
    app.state.keyword_extraction_service = FakeKeywordExtractionService(
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
    assert saved["debug:purpose"] == MENU_PROMOTION_PURPOSE
    assert "draft_keyword:1" not in saved
    assert fake_service.fallback_calls[0]["fallback_source"] is None


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
            content='{"guide_text":"Show the dish clearly.","caption":"Fresh soup for tonight."}',
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
