"""Services for extracting the best frame and uploading draft images."""

from __future__ import annotations

import asyncio
import shutil
from dataclasses import dataclass
from pathlib import Path

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.perfectframe.extractors import BestFrameExtractor
from app.perfectframe.image_processors import OpenCVImage
from app.perfectframe.schemas import ExtractorConfig, Image, ImageExtension
from app.schemas.sessions import ExtractFramesRequest
from app.services.sessions import STATUS_STARTED, STATUS_TEXT_GENERATED, session_key, upsert_content_session

STATUS_FAIL = STATUS_TEXT_GENERATED
STATUS_FRAME_EXTRACTED = "FRAME_EXTRACTED"


@dataclass
class ExtractFramesResult:
    """Result returned by the frame extraction workflow."""

    status: str
    drafts: list[str]
    failure_reason: str | None = None


class S3DraftUploader:
    """Upload extracted draft images to S3 when configured."""

    def __init__(self) -> None:
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return self._settings.s3_configured

    async def upload_frame(
        self,
        session_id: str,
        frame: Image,
        workdir: Path,
        draft_index: int = 1,
    ) -> str | None:
        if not self.is_configured:
            return None

        filename = f"draft-{draft_index:03d}.jpg"
        image_path = await asyncio.to_thread(
            OpenCVImage.save_image,
            frame,
            workdir,
            ImageExtension.JPG,
            filename,
        )
        return await asyncio.to_thread(
            self._upload_file,
            session_id,
            image_path,
            draft_index,
        )

    def _upload_file(self, session_id: str, image_path: Path, draft_index: int) -> str:
        import boto3

        object_key = f"ai-drafts/{session_id}/draft-{draft_index:03d}.jpg"
        client = boto3.client(
            "s3",
            region_name=self._settings.S3_REGION,
            aws_access_key_id=self._settings.S3_ACCESS_KEY,
            aws_secret_access_key=self._settings.S3_SECRET_KEY,
        )
        client.upload_file(
            str(image_path),
            self._settings.S3_BUCKET_NAME,
            object_key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        return f"/{object_key}"


class S3VideoDownloader:
    """Download source videos from S3 using configured credentials."""

    def __init__(self) -> None:
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return self._settings.s3_configured

    async def download_video(self, video_key: str, destination: Path) -> None:
        await asyncio.to_thread(self._download_video, video_key, destination)

    def _download_video(self, video_key: str, destination: Path) -> None:
        import boto3

        client = boto3.client(
            "s3",
            region_name=self._settings.S3_REGION,
            aws_access_key_id=self._settings.S3_ACCESS_KEY,
            aws_secret_access_key=self._settings.S3_SECRET_KEY,
        )
        client.download_file(self._settings.S3_BUCKET_NAME, self._normalize_key(video_key), str(destination))

    @staticmethod
    def _normalize_key(video_key: str) -> str:
        return video_key.lstrip("/")


class FrameExtractionService:
    """Download videos, extract the best frame, and upload it as a draft."""

    def __init__(
        self,
        extractor_config: ExtractorConfig,
        extractor: BestFrameExtractor,
        downloader: S3VideoDownloader,
        uploader: S3DraftUploader,
        temp_root: Path,
    ) -> None:
        self.config = extractor_config
        self.extractor = extractor
        self.downloader = downloader
        self.uploader = uploader
        self.temp_root = temp_root

    async def extract_and_upload(
        self,
        session_id: str,
        video_key: str,
    ) -> ExtractFramesResult:
        session_dir = self.temp_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        video_path = session_dir / "input-video.mp4"

        try:
            if not self.downloader.is_configured or not self.uploader.is_configured:
                return ExtractFramesResult(
                    status=STATUS_FAIL,
                    drafts=[],
                    failure_reason="s3_unavailable",
                )

            await self.downloader.download_video(video_key, video_path)
            frame = await asyncio.to_thread(self.extractor.extract_best_frame, video_path)
            if frame is None:
                return ExtractFramesResult(
                    status=STATUS_FAIL,
                    drafts=[],
                    failure_reason="frame_extraction_failed",
                )

            uploaded_path = await self.uploader.upload_frame(session_id, frame, session_dir)
            if uploaded_path is None:
                return ExtractFramesResult(
                    status=STATUS_FAIL,
                    drafts=[],
                    failure_reason="s3_upload_unavailable",
                )

            return ExtractFramesResult(status=STATUS_FRAME_EXTRACTED, drafts=[uploaded_path])
        except Exception as exc:
            return ExtractFramesResult(
                status=STATUS_FAIL,
                drafts=[],
                failure_reason=str(exc),
            )
        finally:
            shutil.rmtree(session_dir, ignore_errors=True)


def get_frame_extraction_service(request: Request) -> FrameExtractionService:
    """Return the shared frame extraction service from FastAPI state."""

    service = getattr(request.app.state, "frame_extraction_service", None)
    if service is None:
        raise RuntimeError("Frame extraction service is not initialized.")
    return service


async def process_extract_frames(
    session_id: str,
    payload: ExtractFramesRequest,
    redis: Redis,
    frame_service: FrameExtractionService,
) -> ExtractFramesResult:
    """Process a best-frame extraction request and persist session metadata."""

    result = await frame_service.extract_and_upload(
        session_id=session_id,
        video_key=payload.video,
    )

    existing_status = await redis.hget(session_key(session_id), "status")
    redis_payload = {
        "session_id": session_id,
        "video": payload.video,
        "status": result.status if result.status == STATUS_FRAME_EXTRACTED else (existing_status or STATUS_TEXT_GENERATED),
    }

    await upsert_content_session(
        redis,
        session_id,
        scalar_fields=redis_payload,
        drafts=result.drafts,
    )
    return result
