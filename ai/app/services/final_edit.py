"""Services for uploading final images from extracted draft frames."""

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
from app.schemas.sessions import FinalEditRequest
from app.services.final_edit_agent import FinalEditAgent, FinalEditImageState
from app.services.final_edit_planner import (
    FinalEditPlannerClient,
    FinalEditSessionContext,
    build_final_edit_planner_client,
    load_final_edit_session_context,
)
from app.services.final_edit_tools import FinalEditToolRegistry
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
    """Upload final images from extracted draft frames."""

    def __init__(
        self,
        downloader: S3DraftImageDownloader,
        uploader: S3FinalImageUploader,
        temp_root: Path,
        planner_client: FinalEditPlannerClient | None = None,
        agent: FinalEditAgent | None = None,
    ) -> None:
        self.downloader = downloader
        self.uploader = uploader
        self.temp_root = temp_root
        self.planner_client = planner_client or build_final_edit_planner_client()
        self.agent = agent or FinalEditAgent(
            FinalEditToolRegistry(),
            tool_event_sink=self._log_tool_event,
        )

    async def edit_and_upload(
        self,
        session_id: str,
        drafts: list[str],
        context: FinalEditSessionContext | None = None,
    ) -> FinalEditResult:
        session_dir = self.temp_root / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        uploaded_results: list[str] = []
        downloaded_drafts: list[Path] = []
        debug_fields = {
            "debug:draft_count": str(len(drafts)),
            "debug:session_dir": str(session_dir),
        }
        context = context or FinalEditSessionContext(caption="", keywords=[])
        debug_fields["debug:caption_present"] = str(bool(context.caption)).lower()
        debug_fields["debug:keyword_count"] = str(len(context.keywords))
        debug_fields["debug:planner_mode"] = "json_batch"
        planner_fallback = not bool(context.caption or context.keywords)
        plans_by_index = {}

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
                downloaded_drafts.append(draft_path)
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

            logger.info(
                "Loading final edit session context.",
                extra=build_log_extra(
                    "final_edit.load_context.completed",
                    component="final_edit",
                    stage="load_context",
                    session_id=session_id,
                    outcome="succeeded",
                    caption_present=bool(context.caption),
                    keyword_count=len(context.keywords),
                ),
            )

            if not planner_fallback:
                plan_started_at = time.perf_counter()
                logger.info(
                    "Planning final edit sequence.",
                    extra=build_log_extra(
                        "final_edit.plan.started",
                        component="final_edit",
                        stage="plan",
                        session_id=session_id,
                        outcome="started",
                        draft_count=len(downloaded_drafts),
                        keyword_count=len(context.keywords),
                    ),
                )
                try:
                    plans = await self.planner_client.build_plans(
                        [str(path) for path in downloaded_drafts],
                        context,
                    )
                except Exception as exc:
                    planner_fallback = True
                    debug_fields["debug:planner_failure_type"] = exc.__class__.__name__
                    logger.warning(
                        "Final edit planner failed. Falling back to original drafts.",
                        extra=build_log_extra(
                            "final_edit.planner_fallback",
                            component="final_edit",
                            stage="plan",
                            session_id=session_id,
                            outcome="fallback",
                            error_type=exc.__class__.__name__,
                        ),
                    )
                else:
                    plans_by_index = {plan.image_index: plan for plan in plans}
                    logger.info(
                        "Planned final edit sequence.",
                        extra=build_log_extra(
                            "final_edit.plan.completed",
                            component="final_edit",
                            stage="plan",
                            session_id=session_id,
                            outcome="succeeded",
                            planned_image_count=len(plans),
                            elapsed_ms=int((time.perf_counter() - plan_started_at) * 1000),
                        ),
                    )
            else:
                logger.info(
                    "Skipping final edit planner because no text context is available.",
                    extra=build_log_extra(
                        "final_edit.planner_fallback",
                        component="final_edit",
                        stage="plan",
                        session_id=session_id,
                        outcome="fallback",
                        error_type="missing_context",
                    ),
                )

            debug_fields["debug:planner_fallback"] = str(planner_fallback).lower()
            debug_fields["debug:planned_image_count"] = str(len(plans_by_index))

            edited_paths: list[Path] = []
            for image_index, draft_path in enumerate(downloaded_drafts):
                plan = plans_by_index.get(image_index)
                if plan is None:
                    edited_paths.append(draft_path)
                    continue

                debug_fields[f"debug:tool_count:{image_index + 1}"] = str(len(plan.tools))
                debug_fields[f"debug:tools:{image_index + 1}"] = ",".join(plan.tools)
                image_state = await self.agent.run(
                    FinalEditImageState(
                        image_path=draft_path,
                        working_dir=session_dir / "edited",
                        plan=plan,
                        session_id=session_id,
                        final_index=image_index + 1,
                    )
                )
                if image_state.fallback_to_original:
                    debug_fields[f"debug:image_fallback:{image_index + 1}"] = "true"
                    if image_state.failure_reason:
                        debug_fields[f"debug:image_failure:{image_index + 1}"] = (
                            image_state.failure_reason
                        )
                edited_paths.append(image_state.output_path or draft_path)

            for final_index, draft_key in enumerate(drafts, start=1):
                output_path = edited_paths[final_index - 1]
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
                    output_path,
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

    def _log_tool_event(
        self,
        phase: str,
        state: FinalEditImageState,
        tool_name: str,
    ) -> None:
        event_name = f"final_edit.tool.{phase}"
        logger_method = logger.info if phase != "failed" else logger.warning
        logger_method(
            "Final edit tool event.",
            extra=build_log_extra(
                event_name,
                component="final_edit",
                stage="tool",
                session_id=state.session_id,
                final_index=state.final_index,
                tool_name=tool_name,
                outcome="failed" if phase == "failed" else phase,
            ),
        )

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
    logger.info(
        "Loading final edit session context.",
        extra=build_log_extra(
            "final_edit.load_context.started",
            component="final_edit",
            stage="load_context",
            session_id=session_id,
            outcome="started",
        ),
    )
    context = await load_final_edit_session_context(redis, session_id)
    result = await final_edit_service.edit_and_upload(
        session_id=session_id,
        drafts=payload.drafts,
        context=context,
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
