from uuid import uuid4

import fakeredis
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.orientation.predictor import OrientationPredictor
from app.schemas.sessions import ExtractFramesResponse, FinalEditResponse
from app.services.final_edit import FinalEditResult, FinalEditService
from app.services.frame_extraction import ExtractFramesResult
from app.services.keyword_extraction import (
    KeywordExtractionService,
    KeywordExtractionUnavailableError,
)
from app.services.sessions import session_key

VALID_PAYLOAD = {
    "store_id": str(uuid4()),
    "utterance": "warm lighting cozy table signature menu",
    "owner_persona": "aesthetic",
    "date": "2026-04-27",
    "weather": {"condition": "rainy", "temperature": 18.5},
}

VALID_EXTRACT_PAYLOAD = {
    "session_id": str(uuid4()),
    "video": "/inputs/test-session/test-video.mp4",
}


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
        keywords: list[str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.keywords = keywords or ["signature menu", "cozy table"]
        self.error = error
        self.calls: list[str] = []

    async def extract_keywords(self, utterance: str) -> list[str]:
        self.calls.append(utterance)
        if self.error is not None:
            raise self.error
        return self.keywords


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
    assert fake_redis_sync.hgetall(session_key(session_id)) == {}


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

    assert saved["status"] == "TEXT_GENERATED"
    assert saved["caption"]
    assert "#rainy" in saved["caption"]
    keyword_fields = [field for field in saved if field.startswith("keyword:")]
    assert 1 <= len(keyword_fields) <= 3
    assert "session_id" not in saved
    assert "store_id" not in saved
    assert "owner_persona" not in saved
    assert "weather_condition" not in saved
    assert "weather_temperature" not in saved
    assert "date" not in saved
    assert "expires_at" not in saved


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


@pytest.mark.asyncio
async def test_final_edit_service_rolls_back_uploaded_results(tmp_path) -> None:
    uploader = FailingUploader()
    service = FinalEditService(
        predictor=StubPredictor(),
        downloader=StubDraftDownloader(),
        uploader=uploader,
        temp_root=tmp_path,
    )
    session_id = "session-rollback-1"

    result = await service.edit_and_upload(
        session_id=session_id,
        drafts=[
            "/ai-drafts/session-rollback-1/draft-001.jpg",
            "/ai-drafts/session-rollback-1/draft-002.jpg",
        ],
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
    service = KeywordExtractionService(model_path=None)

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


def test_keyword_extraction_service_rejects_non_json_output() -> None:
    service = KeywordExtractionService(model_path=None)

    with pytest.raises(KeywordExtractionUnavailableError):
        service._parse_keywords("\ub9c9\uac78\ub9ac, \ud30c\uc804")


def test_keyword_extraction_service_accepts_keyword_object_payload() -> None:
    service = KeywordExtractionService(model_path=None)

    keywords = service._parse_keywords(
        '{'
        '"keywords": ['
        '"\\ub9c9\\uac78\\ub9ac", '
        '"\\ud30c\\uc804", '
        '"\\ub9e4\\uc7a5"'
        "]}"
    )

    assert keywords == ["\ub9c9\uac78\ub9ac", "\ud30c\uc804"]


@pytest.mark.asyncio
async def test_keyword_extraction_service_raises_when_disabled() -> None:
    service = KeywordExtractionService(model_path=None, enabled=False)

    with pytest.raises(KeywordExtractionUnavailableError):
        await service.extract_keywords(
            "\uc624\ub298 \ub9c9\uac78\ub9ac\ub791 \ud30c\uc804\uc774 \ub531\uc774\ub2e4"
        )
