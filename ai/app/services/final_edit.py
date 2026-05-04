"""Services for draft orientation correction and final image upload."""

from __future__ import annotations

import asyncio
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
import time

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.logging import build_log_extra
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
                logger.warning(
                    "Final edit aborted because S3 is unavailable.",
                    extra=build_log_extra(
                        "final_edit.s3_config_check",
                        component="final_edit",
                        stage="s3_config_check",
                        session_id=session_id,
                        outcome="failed",
                        error_type="s3_unavailable",
                        draft_count=len(drafts),
                    ),
                )
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
                download_started_at = time.perf_counter()
                logger.info(
                    "Downloading draft image for final edit.",
                    extra=build_log_extra(
                        "final_edit.download_draft.started",
                        component="final_edit",
                        stage="download_draft",
                        session_id=session_id,
                        final_index=final_index,
                        draft_key=draft_key,
                        outcome="started",
                    ),
                )
                await self.downloader.download_draft(draft_key, draft_path)
                logger.info(
                    "Downloaded draft image for final edit.",
                    extra=build_log_extra(
                        "final_edit.download_draft.completed",
                        component="final_edit",
                        stage="download_draft",
                        session_id=session_id,
                        final_index=final_index,
                        draft_key=draft_key,
                        outcome="succeeded",
                        elapsed_ms=int((time.perf_counter() - download_started_at) * 1000),
                    ),
                )

                debug_fields["debug:stage"] = f"predict_orientation_{final_index}"
                predict_started_at = time.perf_counter()
                logger.info(
                    "Predicting draft image orientation.",
                    extra=build_log_extra(
                        "final_edit.predict_orientation.started",
                        component="final_edit",
                        stage="predict_orientation",
                        session_id=session_id,
                        final_index=final_index,
                        draft_key=draft_key,
                        outcome="started",
                    ),
                )
                predicted_angle = await asyncio.to_thread(
                    self.predictor.predict_angle,
                    draft_path,
                )
                debug_fields[f"debug:predicted_angle:{final_index}"] = (
                    f"{predicted_angle:.6f}"
                )
                logger.info(
                    "Predicted orientation angle for draft image.",
                    extra=build_log_extra(
                        "final_edit.predict_orientation.completed",
                        component="final_edit",
                        stage="predict_orientation",
                        session_id=session_id,
                        final_index=final_index,
                        draft_key=draft_key,
                        predicted_angle=f"{predicted_angle:.6f}",
                        outcome="succeeded",
                        elapsed_ms=int((time.perf_counter() - predict_started_at) * 1000),
                    ),
                )

                debug_fields["debug:stage"] = f"correct_orientation_{final_index}"
                corrected_path = session_dir / f"final-{final_index:03d}.jpg"
                applied_rotation = -predicted_angle
                correct_started_at = time.perf_counter()
                logger.info(
                    "Applying orientation correction to draft image.",
                    extra=build_log_extra(
                        "final_edit.correct_orientation.started",
                        component="final_edit",
                        stage="correct_orientation",
                        session_id=session_id,
                        final_index=final_index,
                        draft_key=draft_key,
                        predicted_angle=f"{predicted_angle:.6f}",
                        applied_rotation=f"{applied_rotation:.6f}",
                        outcome="started",
                    ),
                )
                await asyncio.to_thread(
                    self.predictor.correct_orientation,
                    draft_path,
                    corrected_path,
                    predicted_angle,
                )
                logger.info(
                    "Orientation correction completed for draft image.",
                    extra=build_log_extra(
                        "final_edit.correct_orientation.completed",
                        component="final_edit",
                        stage="correct_orientation",
                        session_id=session_id,
                        final_index=final_index,
                        draft_key=draft_key,
                        predicted_angle=f"{predicted_angle:.6f}",
                        applied_rotation=f"{applied_rotation:.6f}",
                        outcome="succeeded",
                        elapsed_ms=int((time.perf_counter() - correct_started_at) * 1000),
                    ),
                )

                debug_fields["debug:stage"] = f"upload_final_{final_index}"
                upload_started_at = time.perf_counter()
                logger.info(
                    "Uploading final edited image.",
                    extra=build_log_extra(
                        "final_edit.upload_final.started",
                        component="final_edit",
                        stage="upload_final",
                        session_id=session_id,
                        final_index=final_index,
                        draft_key=draft_key,
                        outcome="started",
                    ),
                )
                uploaded_path = await self.uploader.upload_final(
                    session_id,
                    corrected_path,
                    final_index,
                )
                uploaded_results.append(uploaded_path)
                logger.info(
                    "Uploaded final edited image.",
                    extra=build_log_extra(
                        "final_edit.upload_final.completed",
                        component="final_edit",
                        stage="upload_final",
                        session_id=session_id,
                        final_index=final_index,
                        draft_key=draft_key,
                        outcome="succeeded",
                        uploaded_path=uploaded_path,
                        elapsed_ms=int((time.perf_counter() - upload_started_at) * 1000),
                    ),
                )

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
                extra=build_log_extra(
                    "final_edit.exception",
                    component="final_edit",
                    stage=debug_fields["debug:stage"],
                    session_id=session_id,
                    draft_count=len(drafts),
                    outcome="failed",
                    error_type=exc.__class__.__name__,
                ),
            )
            await self._rollback_uploaded(uploaded_results)
            return FinalEditResult(
                status=STATUS_FAIL,
                results=[],
                failure_reason=str(exc),
                debug_fields=debug_fields,
            )
        finally:
            logger.info(
                "Cleaning up final edit temp directory.",
                extra=build_log_extra(
                    "final_edit.cleanup_tempdir",
                    component="final_edit",
                    stage="cleanup_tempdir",
                    session_id=session_id,
                    outcome="completed",
                    session_dir=str(session_dir),
                ),
            )
            shutil.rmtree(session_dir, ignore_errors=True)

    async def _rollback_uploaded(self, uploaded_results: list[str]) -> None:
        if not uploaded_results:
            return

        for uploaded_path in uploaded_results:
            try:
                logger.info(
                    "Rolling back uploaded final image.",
                    extra=build_log_extra(
                        "final_edit.rollback_delete_final.started",
                        component="final_edit",
                        stage="rollback_delete_final",
                        outcome="started",
                        uploaded_path=uploaded_path,
                    ),
                )
                await self.uploader.delete_final(uploaded_path)
                logger.info(
                    "Rolled back uploaded final image.",
                    extra=build_log_extra(
                        "final_edit.rollback_delete_final.completed",
                        component="final_edit",
                        stage="rollback_delete_final",
                        outcome="succeeded",
                        uploaded_path=uploaded_path,
                    ),
                )
            except Exception:
                logger.warning(
                    "Failed to delete uploaded final image during rollback.",
                    extra=build_log_extra(
                        "final_edit.rollback_delete_final.completed",
                        component="final_edit",
                        stage="rollback_delete_final",
                        outcome="failed",
                        error_type="rollback_delete_failed",
                        uploaded_path=uploaded_path,
                    ),
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
    logger.info(
        "Persisting final edit result to redis.",
        extra=build_log_extra(
            "final_edit.persist_redis.started",
            component="final_edit",
            stage="persist_redis",
            session_id=session_id,
            outcome="started",
            draft_count=len(payload.drafts),
            result_status=result.status,
        ),
    )

    await upsert_content_session(
        redis,
        session_id,
        scalar_fields=redis_payload,
        photos=result.results,
        debug_fields=result.debug_fields,
    )
    logger.info(
        "Persisted final edit result to redis.",
        extra=build_log_extra(
            "final_edit.persist_redis.completed",
            component="final_edit",
            stage="persist_redis",
            session_id=session_id,
            outcome="succeeded",
            photo_count=len(result.results),
            result_status=result.status,
        ),
    )

    if result.status != STATUS_PHOTO_EDITED:
        await redis.hset(session_key(session_id), mapping={"status": STATUS_FAIL})

    return result
