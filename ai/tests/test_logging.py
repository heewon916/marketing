import io
import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import re

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.logging import build_log_extra
from app.main import app
from app.perfectframe.schemas import ExtractorConfig
from app.services.final_edit import FinalEditService
from app.services.frame_extraction import FrameExtractionService


VALID_PAYLOAD = {
    "store_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
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


@contextmanager
def capture_app_logs() -> Iterator[io.StringIO]:
    app_logger = logging.getLogger("app")
    assert app_logger.handlers
    handler = app_logger.handlers[0]
    original_stream = handler.stream
    stream = io.StringIO()
    handler.setStream(stream)
    try:
        yield stream
    finally:
        handler.flush()
        handler.setStream(original_stream)


class StubVideoDownloader:
    is_configured = True

    async def download_video(self, video_key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(video_key.encode("utf-8"))


class StubDraftUploader:
    is_configured = True

    async def upload_frame(self, session_id: str, frame, workdir: Path, draft_index: int = 1) -> str:
        return f"/ai-drafts/{session_id}/draft-{draft_index:03d}.jpg"


class StubFrameExtractor:
    def extract_best_frame(self, video_path: Path):
        return np.zeros((8, 8, 3), dtype=np.uint8)


class StubDraftDownloader:
    is_configured = True

    async def download_draft(self, draft_key: str, destination: Path) -> None:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(draft_key.encode("utf-8"))


class StubFinalUploader:
    is_configured = True

    async def upload_final(self, session_id: str, image_path: Path, final_index: int) -> str:
        return f"/ai-finals/{session_id}/final-{final_index:03d}.jpg"

    async def delete_final(self, uploaded_path: str) -> None:
        return None


def test_formatter_includes_extra_fields_and_redacts_secrets() -> None:
    logger = logging.getLogger("app.tests.logging")

    with capture_app_logs() as stream:
        logger.info(
            "formatter test",
            extra=build_log_extra(
                "test.logging.formatter",
                video_key="/inputs/demo.mp4",
                keyword_count=2,
                s3_secret_key="top-secret",
            ),
        )

    output = stream.getvalue()
    assert 'event="test.logging.formatter"' in output
    assert 'video_key="/inputs/demo.mp4"' in output
    assert "keyword_count=2" in output
    assert 's3_secret_key="<redacted>"' in output


def test_request_logging_uses_same_request_id_for_start_and_finish(client: TestClient) -> None:
    with capture_app_logs() as stream:
        response = client.get("/ai/health")

    assert response.status_code == 200
    request_id = response.headers["x-request-id"]
    output = stream.getvalue()
    started_match = re.search(r'event="http.request.started".*request_id="([^"]+)"', output)
    completed_match = re.search(r'event="http.request.completed".*request_id="([^"]+)"', output)

    assert started_match is not None
    assert completed_match is not None
    assert started_match.group(1) == request_id
    assert completed_match.group(1) == request_id


def test_request_logging_hides_raw_identifiers_when_disabled(client: TestClient) -> None:
    original = settings.LOG_INCLUDE_RAW_IDENTIFIERS
    settings.LOG_INCLUDE_RAW_IDENTIFIERS = False

    try:
        with capture_app_logs() as stream:
            response = client.post(
                "/ai/sessions/log-session-1/process-utterance",
                json=VALID_PAYLOAD,
            )
    finally:
        settings.LOG_INCLUDE_RAW_IDENTIFIERS = original

    assert response.status_code == 200
    output = stream.getvalue()
    assert "utterance_length=39" in output
    assert "utterance_preview=" not in output
    assert "store_id=" not in output


def test_request_logging_includes_raw_identifiers_when_enabled(client: TestClient) -> None:
    original = settings.LOG_INCLUDE_RAW_IDENTIFIERS
    settings.LOG_INCLUDE_RAW_IDENTIFIERS = True

    try:
        with capture_app_logs() as stream:
            response = client.post(
                "/ai/sessions/log-session-2/process-utterance",
                json=VALID_PAYLOAD,
            )
    finally:
        settings.LOG_INCLUDE_RAW_IDENTIFIERS = original

    assert response.status_code == 200
    output = stream.getvalue()
    assert 'utterance_preview="warm lighting cozy table signature menu"' in output
    assert 'store_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"' in output


@pytest.mark.asyncio
async def test_frame_extraction_emits_stage_logs(tmp_path: Path) -> None:
    service = FrameExtractionService(
        extractor_config=ExtractorConfig(input_directory=tmp_path, output_directory=tmp_path),
        extractor=StubFrameExtractor(),
        downloader=StubVideoDownloader(),
        uploader=StubDraftUploader(),
        temp_root=tmp_path,
    )

    with capture_app_logs() as stream:
        result = await service.extract_and_upload(
            session_id="frame-log-session",
            video_key="/inputs/frame-log.mp4",
        )

    assert result.status == "FRAME_EXTRACTED"
    output = stream.getvalue()
    assert 'event="frame_extraction.download_video.started"' in output
    assert 'event="frame_extraction.download_video.completed"' in output
    assert 'event="frame_extraction.extract_frame.started"' in output
    assert 'event="frame_extraction.extract_frame.completed"' in output
    assert 'event="frame_extraction.upload_frame.started"' in output
    assert 'event="frame_extraction.upload_frame.completed"' in output
    assert 'event="frame_extraction.cleanup_tempdir"' in output


@pytest.mark.asyncio
async def test_final_edit_emits_stage_logs(tmp_path: Path) -> None:
    service = FinalEditService(
        downloader=StubDraftDownloader(),
        uploader=StubFinalUploader(),
        temp_root=tmp_path,
    )

    with capture_app_logs() as stream:
        result = await service.edit_and_upload(
            session_id="final-log-session",
            drafts=["/ai-drafts/final-log-session/draft-001.jpg"],
        )

    assert result.status == "PHOTO_EDITED"
    output = stream.getvalue()
    assert 'event="final_edit.download_draft.started"' in output
    assert 'event="final_edit.download_draft.completed"' in output
    assert 'event="final_edit.upload_final.started"' in output
    assert 'event="final_edit.upload_final.completed"' in output
    assert 'event="final_edit.cleanup_tempdir"' in output
