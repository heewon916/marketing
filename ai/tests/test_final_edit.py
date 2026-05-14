import asyncio
from pathlib import Path
from uuid import uuid4

import fakeredis
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas.sessions import FinalEditResponse
from app.bootstrap import _initialize_final_edit_service
from app.services.final_edit import FinalEditResult, FinalEditService
from app.services.final_edit_runtime import FinalEditUnavailableError
from app.services.final_edit_planner import FinalEditSessionContext, ImageEditPlan
from app.services.sessions import session_key
from tests.utils.session_support import (
    CapturingFinalUploader,
    FakeFinalEditService,
    FakePlannerClient,
    FailingPlannerClient,
    FailingUploader,
    FallbackAgent,
    StubDraftDownloader,
    VALID_PAYLOAD,
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
            failure_reason="final_edit_failed",
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


def test_final_edit_returns_503_when_service_is_unavailable(
    client: TestClient,
) -> None:
    original_service = getattr(app.state, "final_edit_service", None)
    original_available = getattr(app.state, "final_edit_available", True)
    original_reason = getattr(app.state, "final_edit_unavailable_reason", None)
    session_id = str(uuid4())
    payload = {
        "session_id": session_id,
        "drafts": ["/ai-drafts/session-123/draft-001.jpg"],
    }
    app.state.final_edit_service = None
    app.state.final_edit_available = False
    app.state.final_edit_unavailable_reason = "FinalEditUnavailableError: OpenCV is unavailable"

    try:
        response = client.post(f"/ai/sessions/{session_id}/final-edit", json=payload)
    finally:
        app.state.final_edit_service = original_service
        app.state.final_edit_available = original_available
        app.state.final_edit_unavailable_reason = original_reason

    assert response.status_code == 503
    assert response.json()["detail"] == "Final edit is unavailable."


def test_initialize_final_edit_service_marks_unavailable_on_opencv_error(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    startup_app = FastAPI()

    def fail_import_cv2():
        raise FinalEditUnavailableError("OpenCV is unavailable for final edit.")

    monkeypatch.setattr("app.bootstrap.import_cv2", fail_import_cv2)

    _initialize_final_edit_service(startup_app, tmp_path)

    assert startup_app.state.final_edit_service is None
    assert startup_app.state.final_edit_planner_client is None
    assert startup_app.state.final_edit_available is False
    assert (
        startup_app.state.final_edit_unavailable_reason
        == "FinalEditUnavailableError: OpenCV is unavailable for final edit."
    )


def test_final_edit_response_limits_results_to_three() -> None:
    with pytest.raises(ValidationError):
        FinalEditResponse(
            session_id="sess",
            status="PHOTO_EDITED",
            results=["1", "2", "3", "4"],
        )


def test_final_edit_service_rolls_back_uploaded_results(tmp_path: Path) -> None:
    uploader = FailingUploader()
    service = FinalEditService(
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


def test_final_edit_service_marks_planner_fallback_on_planner_error(tmp_path: Path) -> None:
    uploader = CapturingFinalUploader()
    service = FinalEditService(
        downloader=StubDraftDownloader(),
        uploader=uploader,
        temp_root=tmp_path,
        planner_client=FailingPlannerClient(),
    )

    result = asyncio.run(
        service.edit_and_upload(
            session_id="session-planner-fallback-1",
            drafts=["/ai-drafts/session-planner-fallback-1/draft-001.jpg"],
            context=FinalEditSessionContext(
                caption="\ucfc4\ub81b \ucf00\uc774\ud06c \uc18c\uac1c",
                keywords=["\ucf00\uc774\ud06c"],
            ),
        )
    )

    assert result.status == "PHOTO_EDITED"
    assert result.results == ["/ai-finals/session-planner-fallback-1/final-001.jpg"]
    assert result.debug_fields is not None
    assert result.debug_fields["debug:planner_fallback"] == "true"
    assert result.debug_fields["debug:planner_failure_type"] == "RuntimeError"
    assert result.debug_fields["debug:planner_response_received"] == "false"
    assert result.debug_fields["debug:planned_indexes"] == ""
    assert result.debug_fields["debug:executed_tools:1"] == ""
    assert result.debug_fields["debug:upload_source_kind:1"] == "original_fallback"
    assert result.debug_fields["debug:output_path:1"].endswith("draft-001.jpg")
    assert uploader.source_paths[0].endswith("draft-001.jpg")


def test_final_edit_service_marks_image_fallback_when_agent_falls_back(tmp_path: Path) -> None:
    uploader = CapturingFinalUploader()
    service = FinalEditService(
        downloader=StubDraftDownloader(),
        uploader=uploader,
        temp_root=tmp_path,
        planner_client=FakePlannerClient(
            [
                ImageEditPlan(
                    image_index=0,
                    content="\ucf00\uc774\ud06c",
                    strategy="\ub178\uc774\uc988 \uc815\ub9ac",
                    tools=["denoise"],
                    params={"denoise": {"strength": 0.4}},
                )
            ]
        ),
        agent=FallbackAgent(),
    )

    result = asyncio.run(
        service.edit_and_upload(
            session_id="session-image-fallback-1",
            drafts=["/ai-drafts/session-image-fallback-1/draft-001.jpg"],
            context=FinalEditSessionContext(
                caption="\ucfc4\ub81b \ucf00\uc774\ud06c \uc18c\uac1c",
                keywords=["\ucf00\uc774\ud06c"],
            ),
        )
    )

    assert result.status == "PHOTO_EDITED"
    assert result.debug_fields is not None
    assert result.debug_fields["debug:planner_response_received"] == "true"
    assert result.debug_fields["debug:planned_indexes"] == "0"
    assert result.debug_fields["debug:image_fallback:1"] == "true"
    assert result.debug_fields["debug:image_failure:1"] == "tool_failed:denoise:RuntimeError"
    assert result.debug_fields["debug:executed_tools:1"] == ""
    assert result.debug_fields["debug:upload_source_kind:1"] == "original_fallback"
    assert result.debug_fields["debug:output_path:1"].endswith("draft-001.jpg")
    assert uploader.source_paths[0].endswith("draft-001.jpg")


def test_final_edit_service_marks_edited_upload_source_when_agent_succeeds(tmp_path: Path) -> None:
    uploader = CapturingFinalUploader()
    service = FinalEditService(
        downloader=StubDraftDownloader(),
        uploader=uploader,
        temp_root=tmp_path,
        planner_client=FakePlannerClient(
            [
                ImageEditPlan(
                    image_index=0,
                    content="\ucf00\uc774\ud06c",
                    strategy="\ub178\uc774\uc988\ub97c \uc904\uc774\uace0 \uc120\uba85\ub3c4\ub97c \ub192\uc774\uae30",
                    tools=["denoise", "sharpen"],
                    params={
                        "denoise": {"strength": 0.4},
                        "sharpen": {"strength": 0.3},
                    },
                )
            ]
        ),
    )

    result = asyncio.run(
        service.edit_and_upload(
            session_id="session-edited-upload-1",
            drafts=["/ai-drafts/session-edited-upload-1/draft-001.jpg"],
            context=FinalEditSessionContext(
                caption="\ub514\uc800\ud2b8 \ucf00\uc774\ud06c \uc18c\uac1c",
                keywords=["\ucf00\uc774\ud06c"],
            ),
        )
    )

    assert result.status == "PHOTO_EDITED"
    assert result.debug_fields is not None
    assert result.debug_fields["debug:planner_response_received"] == "true"
    assert result.debug_fields["debug:planned_indexes"] == "0"
    assert result.debug_fields["debug:executed_tools:1"] == "denoise,sharpen"
    assert result.debug_fields["debug:upload_source_kind:1"] == "edited"
    assert "edited-000.jpg" in result.debug_fields["debug:output_path:1"]
    assert "edited-000.jpg" in uploader.source_paths[0]
