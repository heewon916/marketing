from uuid import uuid4

import fakeredis
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.sessions import ExtractFramesResponse
from app.services.frame_extraction import ExtractFramesResult
from app.services.sessions import session_key

VALID_PAYLOAD = {
    "store_id": str(uuid4()),
    "utterance": "warm lighting cozy table signature menu",
    "owner_persona": "aesthetic",
    "date": "2026-04-27",
    "weather": {"condition": "rainy", "temperature": 18.5},
}

VALID_EXTRACT_PAYLOAD = {
    "store_id": str(uuid4()),
    "input_video_s3_url": "https://s3-bucket/input/store-video.mp4",
}


class FakeFrameExtractionService:
    def __init__(self, result: ExtractFramesResult) -> None:
        self.result = result
        self.calls: list[tuple[str, str]] = []

    async def extract_and_upload(
        self,
        session_id: str,
        input_video_url: str,
    ) -> ExtractFramesResult:
        self.calls.append((session_id, input_video_url))
        return self.result


def test_process_utterance_returns_session_id_and_guide(client: TestClient) -> None:
    session_id = "redis-session-id-123"

    response = client.post(
        f"/ai/sessions/{session_id}/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert isinstance(body["guide_text"], str)
    assert len(body["guide_text"]) > 0


def test_keywords_hidden_when_debug_off(client: TestClient) -> None:
    response = client.post(
        "/ai/sessions/sess-1/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200
    assert "keywords" not in response.json()


def test_keywords_exposed_when_debug_on(
    client: TestClient, debug_mode: None
) -> None:
    response = client.post(
        "/ai/sessions/sess-2/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200
    body = response.json()
    assert "keywords" in body
    assert isinstance(body["keywords"], list)
    assert len(body["keywords"]) > 0


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
    payload["weather"] = {"condition": "rainy", "temperature": "hot"}

    response = client.post(
        "/ai/sessions/sess-5/process-utterance",
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

    assert saved["session_id"] == session_id
    assert saved["store_id"] == VALID_PAYLOAD["store_id"]
    assert saved["status"] == "TEXT_GENERATED"
    assert saved["caption"]
    assert saved["owner_persona"] == "aesthetic"
    assert saved["weather_condition"] == "rainy"
    assert saved["weather_temperature"] == "18.5"
    assert saved["date"] == "2026-04-27"
    assert "expires_at" in saved
    keyword_fields = [field for field in saved if field.startswith("keyword:")]
    assert keyword_fields


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
    fake_service = FakeFrameExtractionService(
        ExtractFramesResult(
            status="SUCESS",
            drafts=["https://s3-bucket/ai-drafts/session-123/draft-001.jpg"],
        )
    )
    app.state.frame_extraction_service = fake_service
    session_id = "extract-session-1"

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/extract-frames",
            json=VALID_EXTRACT_PAYLOAD,
        )
    finally:
        app.state.frame_extraction_service = original_service

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert body["status"] == "SUCESS"
    assert body["drafts"] == ["https://s3-bucket/ai-drafts/session-123/draft-001.jpg"]
    assert fake_service.calls == [
        (session_id, VALID_EXTRACT_PAYLOAD["input_video_s3_url"])
    ]

    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["status"] == "FRAME_EXTRACTED"
    assert saved["draft:1"] == "https://s3-bucket/ai-drafts/session-123/draft-001.jpg"
    assert saved["store_id"] == VALID_EXTRACT_PAYLOAD["store_id"]
    assert saved["video"] == VALID_EXTRACT_PAYLOAD["input_video_s3_url"]


def test_extract_frames_returns_fail_when_service_fails(
    client: TestClient,
    fake_redis_sync: fakeredis.FakeStrictRedis,
) -> None:
    original_service = app.state.frame_extraction_service
    fake_service = FakeFrameExtractionService(
        ExtractFramesResult(
            status="FAIL",
            drafts=[],
            failure_reason="s3_upload_unavailable",
        )
    )
    app.state.frame_extraction_service = fake_service
    session_id = "extract-session-2"

    try:
        response = client.post(
            f"/ai/sessions/{session_id}/extract-frames",
            json=VALID_EXTRACT_PAYLOAD,
        )
    finally:
        app.state.frame_extraction_service = original_service

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "FAIL"
    assert body["drafts"] == []

    saved = fake_redis_sync.hgetall(session_key(session_id))
    assert saved["status"] == "STARTED"
    assert "draft:1" not in saved
    assert saved["video"] == VALID_EXTRACT_PAYLOAD["input_video_s3_url"]


def test_extract_frames_rejects_invalid_url(client: TestClient) -> None:
    payload = dict(VALID_EXTRACT_PAYLOAD)
    payload["input_video_s3_url"] = "not-a-url"

    response = client.post(
        "/ai/sessions/extract-session-3/extract-frames",
        json=payload,
    )

    assert response.status_code == 422


def test_extract_frames_response_limits_drafts_to_three() -> None:
    with pytest.raises(ValidationError):
        ExtractFramesResponse(
            session_id="sess",
            status="SUCESS",
            drafts=["1", "2", "3", "4"],
        )


def test_frame_extraction_singletons_initialized_on_app_state(
    client: TestClient,
) -> None:
    assert app.state.frame_extractor_config is not None
    assert app.state.best_frame_extractor is not None
    assert app.state.frame_extraction_service is not None
    assert app.state.frame_extraction_service.extractor is app.state.best_frame_extractor
