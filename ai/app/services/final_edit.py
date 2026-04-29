"""Services for draft orientation correction and final image upload."""

from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.orientation.predictor import OrientationPredictor
from app.schemas.sessions import FinalEditRequest
from app.services.sessions import session_key, upsert_content_session

STATUS_FAIL = "FRAME_EXTRACTED"
STATUS_PHOTO_EDITED = "PHOTO_EDITED"
logger = logging.getLogger(__name__)


@dataclass
class FinalEditResult:
    status: str
    results: list[str]
    failure_reason: str | None = None
    debug_fields: dict[str, str] | None = None


class S3DraftImageDownloader:
    """Download extracted draft images from S3."""

    def __init__(self) -> None:
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return self._settings.s3_configured

    async def download_draft(self, draft_key: str, destination: Path) -> None:
        await asyncio.to_thread(self._download_draft, draft_key, destination)

    def _download_draft(self, draft_key: str, destination: Path) -> None:
        import boto3

        destination.parent.mkdir(parents=True, exist_ok=True)
        client = boto3.client(
            "s3",
            region_name=self._settings.S3_REGION,
            aws_access_key_id=self._settings.S3_ACCESS_KEY,
            aws_secret_access_key=self._settings.S3_SECRET_KEY,
        )
        client.download_file(
            self._settings.S3_BUCKET_NAME,
            self._normalize_key(draft_key),
            str(destination),
        )

    @staticmethod
    def _normalize_key(draft_key: str) -> str:
        return draft_key.lstrip("/")


class S3FinalImageUploader:
    """Upload corrected final images to S3 and delete them during rollback."""

    def __init__(self) -> None:
        self._settings = settings

    @property
    def is_configured(self) -> bool:
        return self._settings.s3_configured

    async def upload_final(
        self,
        session_id: str,
        image_path: Path,
        final_index: int,
    ) -> str:
        return await asyncio.to_thread(
            self._upload_final,
            session_id,
            image_path,
            final_index,
        )

    async def delete_final(self, uploaded_path: str) -> None:
        await asyncio.to_thread(self._delete_final, uploaded_path)

    def _upload_final(
        self,
        session_id: str,
        image_path: Path,
        final_index: int,
    ) -> str:
        import boto3

        object_key = f"ai-finals/{session_id}/final-{final_index:03d}.jpg"
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

    def _delete_final(self, uploaded_path: str) -> None:
        import boto3

        client = boto3.client(
            "s3",
            region_name=self._settings.S3_REGION,
            aws_access_key_id=self._settings.S3_ACCESS_KEY,
            aws_secret_access_key=self._settings.S3_SECRET_KEY,
        )
        client.delete_object(
            Bucket=self._settings.S3_BUCKET_NAME,
            Key=uploaded_path.lstrip("/"),
        )


class FinalEditService:
    """Correct draft image orientation and upload final images."""

    def __init__(
        self,
        predictor: OrientationPredictor,
        downloader: S3DraftImageDownloader,
        uploader: S3FinalImageUploader,
        temp_root: Path,
    ) -> None:
        self.predictor = predictor
        self.downloader = downloader
        self.uploader = uploader
        self.temp_root = temp_root

    async def edit_and_upload(
        self,
        session_id: str,
        drafts: list[str],
    ) -> FinalEditResult:
        session_dir = self.temp_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        uploaded_results: list[str] = []
        debug_fields = {
            "debug:draft_count": str(len(drafts)),
            "debug:session_dir": str(session_dir),
        }

        try:
            if not self.downloader.is_configured or not self.uploader.is_configured:
                debug_fields["debug:stage"] = "s3_config_check"
                debug_fields["debug:s3_downloader_configured"] = str(
                    self.downloader.is_configured
                ).lower()
                debug_fields["debug:s3_uploader_configured"] = str(
                    self.uploader.is_configured
                ).lower()
                return FinalEditResult(
                    status=STATUS_FAIL,
                    results=[],
                    failure_reason="s3_unavailable",
                    debug_fields=debug_fields,
                )

            for final_index, draft_key in enumerate(drafts, start=1):
                debug_fields["debug:stage"] = f"download_draft_{final_index}"
                debug_fields[f"debug:draft_key:{final_index}"] = draft_key
                draft_path = session_dir / f"draft-{final_index:03d}.jpg"
                await self.downloader.download_draft(draft_key, draft_path)

                debug_fields["debug:stage"] = f"predict_orientation_{final_index}"
                predicted_angle = await asyncio.to_thread(
                    self.predictor.predict_angle,
                    draft_path,
                )
                debug_fields[f"debug:predicted_angle:{final_index}"] = (
                    f"{predicted_angle:.6f}"
                )
                logger.info(
                    "Predicted orientation angle for draft image.",
                    extra={
                        "session_id": session_id,
                        "final_index": final_index,
                        "draft_key": draft_key,
                        "predicted_angle": f"{predicted_angle:.6f}",
                    },
                )

                debug_fields["debug:stage"] = f"correct_orientation_{final_index}"
                corrected_path = session_dir / f"final-{final_index:03d}.jpg"
                applied_rotation = -predicted_angle
                logger.info(
                    "Applying orientation correction to draft image.",
                    extra={
                        "session_id": session_id,
                        "final_index": final_index,
                        "draft_key": draft_key,
                        "predicted_angle": f"{predicted_angle:.6f}",
                        "applied_rotation": f"{applied_rotation:.6f}",
                    },
                )
                await asyncio.to_thread(
                    self.predictor.correct_orientation,
                    draft_path,
                    corrected_path,
                    predicted_angle,
                )

                debug_fields["debug:stage"] = f"upload_final_{final_index}"
                uploaded_path = await self.uploader.upload_final(
                    session_id,
                    corrected_path,
                    final_index,
                )
                uploaded_results.append(uploaded_path)

            debug_fields["debug:stage"] = "completed"
            return FinalEditResult(
                status=STATUS_PHOTO_EDITED,
                results=uploaded_results,
                debug_fields=debug_fields,
            )
        except Exception as exc:
            debug_fields["debug:stage"] = "exception"
            debug_fields["debug:exception_type"] = exc.__class__.__name__
            debug_fields["debug:exception_message"] = str(exc)
            logger.exception(
                "Final edit failed with an exception.",
                extra={"session_id": session_id, "draft_count": len(drafts)},
            )
            await self._rollback_uploaded(uploaded_results)
            return FinalEditResult(
                status=STATUS_FAIL,
                results=[],
                failure_reason=str(exc),
                debug_fields=debug_fields,
            )
        finally:
            shutil.rmtree(session_dir, ignore_errors=True)

    async def _rollback_uploaded(self, uploaded_results: list[str]) -> None:
        if not uploaded_results:
            return

        for uploaded_path in uploaded_results:
            try:
                await self.uploader.delete_final(uploaded_path)
            except Exception:
                logger.warning(
                    "Failed to delete uploaded final image during rollback.",
                    extra={"uploaded_path": uploaded_path},
                    exc_info=True,
                )


def get_final_edit_service(request: Request) -> FinalEditService:
    service = getattr(request.app.state, "final_edit_service", None)
    if service is None:
        raise RuntimeError("Final edit service is not initialized.")
    return service


async def process_final_edit(
    session_id: str,
    payload: FinalEditRequest,
    redis: Redis,
    final_edit_service: FinalEditService,
) -> FinalEditResult:
    result = await final_edit_service.edit_and_upload(
        session_id=session_id,
        drafts=payload.drafts,
    )

    redis_payload = {
        "session_id": session_id,
        "status": result.status,
    }
    if payload.drafts:
        redis_payload["draft_count"] = str(len(payload.drafts))

    await upsert_content_session(
        redis,
        session_id,
        scalar_fields=redis_payload,
        photos=result.results,
        debug_fields=result.debug_fields,
    )

    if result.status != STATUS_PHOTO_EDITED:
        await redis.hset(session_key(session_id), mapping={"status": STATUS_FAIL})

    return result
