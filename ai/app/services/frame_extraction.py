"""Services for extracting the best frame and uploading draft images."""

from __future__ import annotations

import asyncio
import json
import shutil
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from urllib.request import urlopen

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.perfectframe.extractors import BestFrameExtractor
from app.perfectframe.image_processors import OpenCVImage
from app.perfectframe.schemas import ExtractorConfig, Image, ImageExtension
from app.schemas.sessions import ExtractFramesRequest
from app.services.sessions import session_key

STATUS_SUCESS = "SUCESS"
STATUS_FAIL = "FAIL"


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
    ) -> str | None:
        if not self.is_configured:
            return None

        image_path = await asyncio.to_thread(
            OpenCVImage.save_image,
            frame,
            workdir,
            ImageExtension.JPG,
            "draft-001.jpg",
        )
        return await asyncio.to_thread(self._upload_file, session_id, image_path)

    def _upload_file(self, session_id: str, image_path: Path) -> str:
        import boto3

        object_key = f"ai-drafts/{session_id}/draft-001.jpg"
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
        return self._build_public_url(object_key)

    def _build_public_url(self, object_key: str) -> str:
        if self._settings.CLOUDFRONT_DOMAIN:
            return f"https://{self._settings.CLOUDFRONT_DOMAIN.strip('/')}/{object_key}"
        if self._settings.S3_REGION == "us-east-1":
            return f"https://{self._settings.S3_BUCKET_NAME}.s3.amazonaws.com/{object_key}"
        return (
            f"https://{self._settings.S3_BUCKET_NAME}.s3."
            f"{self._settings.S3_REGION}.amazonaws.com/{object_key}"
        )


class FrameExtractionService:
    """Download videos, extract the best frame, and upload it as a draft."""

    def __init__(
        self,
        extractor_config: ExtractorConfig,
        extractor: BestFrameExtractor,
        uploader: S3DraftUploader,
        temp_root: Path,
    ) -> None:
        self.config = extractor_config
        self.extractor = extractor
        self.uploader = uploader
        self.temp_root = temp_root

    async def extract_and_upload(
        self,
        session_id: str,
        input_video_url: str,
    ) -> ExtractFramesResult:
        session_dir = self.temp_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        video_path = session_dir / "input-video.mp4"

        try:
            await asyncio.to_thread(self._download_video, input_video_url, video_path)
            frame = await asyncio.to_thread(self.extractor.extract_best_frame, video_path)
            if frame is None:
                return ExtractFramesResult(
                    status=STATUS_FAIL,
                    drafts=[],
                    failure_reason="frame_extraction_failed",
                )

            uploaded_url = await self.uploader.upload_frame(session_id, frame, session_dir)
            if uploaded_url is None:
                return ExtractFramesResult(
                    status=STATUS_FAIL,
                    drafts=[],
                    failure_reason="s3_upload_unavailable",
                )

            return ExtractFramesResult(status=STATUS_SUCESS, drafts=[uploaded_url])
        except Exception as exc:
            return ExtractFramesResult(
                status=STATUS_FAIL,
                drafts=[],
                failure_reason=str(exc),
            )
        finally:
            shutil.rmtree(session_dir, ignore_errors=True)

    @staticmethod
    def _download_video(input_video_url: str, destination: Path) -> None:
        with urlopen(input_video_url) as response:
            destination.write_bytes(response.read())


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
        input_video_url=str(payload.input_video_s3_url),
    )

    ttl = settings.SESSION_TTL_SECONDS
    expires_at = (datetime.now(UTC) + timedelta(seconds=ttl)).isoformat()
    redis_payload = {
        "session_id": session_id,
        "store_id": str(payload.store_id),
        "input_video_s3_url": str(payload.input_video_s3_url),
        "status": result.status,
        "drafts": result.drafts,
        "expires_at": expires_at,
    }
    if result.failure_reason:
        redis_payload["failure_reason"] = result.failure_reason

    await redis.set(
        session_key(session_id),
        json.dumps(redis_payload, ensure_ascii=False),
        ex=ttl,
    )
    return result
