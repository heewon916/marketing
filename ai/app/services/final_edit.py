"""Services for uploading final images from extracted draft frames."""

from __future__ import annotations

import asyncio
import json
import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
import time
from typing import TYPE_CHECKING

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.logging import build_log_extra, preview_text
from app.schemas.sessions import FinalEditRequest
from app.services.final_edit_planner import (
    FinalEditPlannerClient,
    FinalEditSessionContext,
    ImageEditPlan,
    build_upscale_only_plan,
    build_final_edit_planner_client,
    load_final_edit_session_context,
    normalize_image_edit_plan,
    resolve_owner_persona_preset,
)
from app.services.final_edit_runtime import (
    FinalEditUnavailableError,
    import_cv2,
)
from app.services.s3_support import build_s3_client, normalize_s3_key
from app.services.sessions import session_key, upsert_content_session

if TYPE_CHECKING:
    from app.services.final_edit_agent import FinalEditAgent, FinalEditImageState

STATUS_FAIL = "FRAME_EXTRACTED"
STATUS_PHOTO_EDITED = "PHOTO_EDITED"
logger = logging.getLogger(__name__)
_PREVIEW_MAX_LENGTH = 120
_PRE_UPSCALE_FILTER_TOOLS = {"color_grading", "sharpen", "background_blur"}


def _build_default_agent(tool_event_sink):
    from app.services.final_edit_agent import FinalEditAgent
    from app.services.final_edit_tools import FinalEditToolRegistry

    return FinalEditAgent(
        FinalEditToolRegistry(),
        tool_event_sink=tool_event_sink,
    )


@dataclass
class FinalEditResult:
    status: str
    results: list[str]
    failure_reason: str | None = None
    debug_fields: dict[str, str] | None = None


def _preview_or_empty(value: str, max_length: int = _PREVIEW_MAX_LENGTH) -> str:
    normalized = value.strip()
    if not normalized:
        return ""
    return preview_text(normalized, max_length)


def _preview_keywords(keywords: list[str], max_length: int = _PREVIEW_MAX_LENGTH) -> str:
    if not keywords:
        return ""
    return preview_text(", ".join(keywords), max_length)


def _determine_output_source(output_path: Path, draft_path: Path) -> str:
    try:
        if output_path.resolve() == draft_path.resolve():
            return "original_fallback"
    except OSError:
        if output_path == draft_path:
            return "original_fallback"
    return "edited"


def _read_image_dimensions(image_path: Path) -> tuple[int | None, int | None]:
    cv2 = import_cv2()
    image = cv2.imread(str(image_path))
    if image is None:
        return None, None
    height, width = image.shape[:2]
    return width, height


def _json_debug_value(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _resolve_image_suffix(image_path: str, default_suffix: str = ".png") -> str:
    suffix = Path(normalize_s3_key(image_path)).suffix.lower()
    return suffix or default_suffix


def _ensure_filter_before_upscale(
    plan: ImageEditPlan,
    owner_persona: str,
) -> ImageEditPlan:
    plan = normalize_image_edit_plan(plan)
    if "upscale" not in plan.tools:
        return plan

    upscale_index = plan.tools.index("upscale")
    has_filter_before_upscale = any(
        tool_name in _PRE_UPSCALE_FILTER_TOOLS for tool_name in plan.tools[:upscale_index]
    )
    if has_filter_before_upscale:
        return plan

    fallback_plan = build_upscale_only_plan(
        plan.image_index,
        owner_persona=owner_persona,
        content=plan.content,
        strategy=plan.strategy,
    )
    fallback_params = dict(fallback_plan.params["color_grading"])
    merged_params = dict(plan.params)
    merged_params["color_grading"] = dict(merged_params.get("color_grading", fallback_params))
    merged_params["upscale"] = dict(merged_params.get("upscale", {"scale": 2}))

    enforced_tools: list[str] = []
    inserted_filter = False
    for tool_name in plan.tools:
        if tool_name == "upscale" and not inserted_filter:
            enforced_tools.append("color_grading")
            inserted_filter = True
        enforced_tools.append(tool_name)

    return normalize_image_edit_plan(
        ImageEditPlan(
            image_index=plan.image_index,
            content=plan.content,
            strategy=plan.strategy,
            tools=enforced_tools,
            params=merged_params,
        )
    )


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
        destination.parent.mkdir(parents=True, exist_ok=True)
        client = build_s3_client()
        client.download_file(
            self._settings.S3_BUCKET_NAME,
            normalize_s3_key(draft_key),
            str(destination),
        )


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
        object_key = f"ai-finals/{session_id}/final-{final_index:03d}.png"
        client = build_s3_client()
        client.upload_file(
            str(image_path),
            self._settings.S3_BUCKET_NAME,
            object_key,
            ExtraArgs={"ContentType": "image/png"},
        )
        return f"/{object_key}"

    def _delete_final(self, uploaded_path: str) -> None:
        client = build_s3_client()
        client.delete_object(
            Bucket=self._settings.S3_BUCKET_NAME,
            Key=normalize_s3_key(uploaded_path),
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
        self.agent = agent or _build_default_agent(self._log_tool_event)

    @staticmethod
    def _build_debug_fields(
        session_dir: Path,
        drafts: list[str],
        context: FinalEditSessionContext,
    ) -> dict[str, str]:
        preset_persona, _, preset_fallback = resolve_owner_persona_preset(
            context.owner_persona
        )
        return {
            "debug:draft_count": str(len(drafts)),
            "debug:session_dir": str(session_dir),
            "debug:owner_persona": context.owner_persona,
            "debug:target_preset_persona": preset_persona,
            "debug:target_preset_fallback": str(preset_fallback).lower(),
            "debug:caption_present": str(bool(context.caption)).lower(),
            "debug:keyword_count": str(len(context.keywords)),
            "debug:planner_mode": "json_batch",
            "debug:planner_response_received": "false",
            "debug:planned_indexes": "",
        }

    def _s3_failure_result(
        self,
        session_id: str,
        drafts: list[str],
        debug_fields: dict[str, str],
    ) -> FinalEditResult:
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

    async def _download_drafts(
        self,
        session_id: str,
        drafts: list[str],
        session_dir: Path,
        debug_fields: dict[str, str],
    ) -> list[Path]:
        downloaded_drafts: list[Path] = []
        for final_index, draft_key in enumerate(drafts, start=1):
            debug_fields["debug:stage"] = f"download_draft_{final_index}"
            debug_fields[f"debug:draft_key:{final_index}"] = draft_key
            suffix = _resolve_image_suffix(draft_key)
            draft_path = session_dir / f"draft-{final_index:03d}{suffix}"
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
        return downloaded_drafts

    async def _plan_images(
        self,
        session_id: str,
        context: FinalEditSessionContext,
        downloaded_drafts: list[Path],
        debug_fields: dict[str, str],
    ) -> tuple[bool, dict[int, object]]:
        planner_fallback = not bool(context.caption or context.keywords)
        plans_by_index: dict[int, object] = {}

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
                caption_preview=_preview_or_empty(context.caption),
                keyword_preview=_preview_keywords(context.keywords),
            ),
        )

        if planner_fallback:
            logger.info(
                "Skipping final edit planner because no text context is available.",
                extra=build_log_extra(
                    "final_edit.planner_fallback",
                    component="final_edit",
                    stage="plan",
                    session_id=session_id,
                    outcome="fallback",
                    error_type="missing_context",
                    planner_fallback_reason="missing_context",
                    caption_present=bool(context.caption),
                    keyword_count=len(context.keywords),
                    downloaded_draft_count=len(downloaded_drafts),
                ),
            )
        else:
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
                debug_fields["debug:planner_response_received"] = str(
                    bool(getattr(self.planner_client, "last_raw_output", None))
                ).lower()
                logger.warning(
                    "Final edit planner failed. Falling back to original drafts.",
                    extra=build_log_extra(
                        "final_edit.planner_fallback",
                        component="final_edit",
                        stage="plan",
                        session_id=session_id,
                        outcome="fallback",
                        error_type=exc.__class__.__name__,
                        planner_fallback_reason="planner_exception",
                        caption_present=bool(context.caption),
                        keyword_count=len(context.keywords),
                        downloaded_draft_count=len(downloaded_drafts),
                    ),
                )
            else:
                plans_by_index = {
                    plan.image_index: normalize_image_edit_plan(plan) for plan in plans
                }
                debug_fields["debug:planner_response_received"] = str(
                    bool(getattr(self.planner_client, "last_raw_output", None))
                ).lower()
                debug_fields["debug:planned_indexes"] = ",".join(
                    str(plan.image_index) for plan in plans_by_index.values()
                )
                logger.info(
                    "Planned final edit sequence.",
                    extra=build_log_extra(
                        "final_edit.plan.completed",
                        component="final_edit",
                        stage="plan",
                        session_id=session_id,
                        outcome="succeeded",
                        planned_image_count=len(plans_by_index),
                        planned_indexes=[
                            plan.image_index for plan in plans_by_index.values()
                        ],
                        planned_tools_by_image={
                            str(plan.image_index): plan.tools
                            for plan in plans_by_index.values()
                        },
                        planned_strategy_preview_by_image={
                            str(plan.image_index): _preview_or_empty(plan.strategy)
                            for plan in plans_by_index.values()
                        },
                        caption_preview=_preview_or_empty(context.caption),
                        keyword_preview=_preview_keywords(context.keywords),
                        planner_response_preview=_preview_or_empty(
                            getattr(self.planner_client, "last_raw_output", "") or ""
                        ),
                        elapsed_ms=int((time.perf_counter() - plan_started_at) * 1000),
                    ),
                )

        debug_fields["debug:planner_fallback"] = str(planner_fallback).lower()
        debug_fields["debug:planned_image_count"] = str(len(plans_by_index))
        return planner_fallback, plans_by_index

    async def _process_images(
        self,
        session_id: str,
        session_dir: Path,
        downloaded_drafts: list[Path],
        plans_by_index: dict[int, object],
        planner_fallback: bool,
        context: FinalEditSessionContext,
        debug_fields: dict[str, str],
    ) -> list[Path]:
        from app.services.final_edit_agent import FinalEditImageState

        edited_paths: list[Path] = []
        for image_index, draft_path in enumerate(downloaded_drafts):
            plan = plans_by_index.get(image_index)
            if plan is None:
                fallback_reason = (
                    "planner_fallback" if planner_fallback else "plan_missing_for_image"
                )
                plan = build_upscale_only_plan(
                    image_index,
                    owner_persona=context.owner_persona,
                    content="draft image",
                    strategy=(
                        "Planner fallback; apply minimum color grading before "
                        "mandatory Real-ESRGAN upscale."
                        if planner_fallback
                        else "No plan returned for this image; apply minimum color "
                        "grading before mandatory Real-ESRGAN upscale."
                    ),
                )
                debug_fields[f"debug:plan_source:{image_index + 1}"] = fallback_reason
            else:
                plan = _ensure_filter_before_upscale(plan, context.owner_persona)

            debug_fields[f"debug:tool_count:{image_index + 1}"] = str(len(plan.tools))
            debug_fields[f"debug:tools:{image_index + 1}"] = ",".join(plan.tools)
            image_state = await self.agent.run(
                FinalEditImageState(
                    image_path=draft_path,
                    working_dir=session_dir / "edited",
                    plan=plan,
                    owner_persona=context.owner_persona,
                    session_id=session_id,
                    final_index=image_index + 1,
                )
            )
            output_path = image_state.output_path or draft_path
            output_source = _determine_output_source(output_path, draft_path)
            debug_fields[f"debug:executed_tools:{image_index + 1}"] = ",".join(
                image_state.executed_tools
            )
            debug_fields[f"debug:upload_source_kind:{image_index + 1}"] = output_source
            debug_fields[f"debug:output_path:{image_index + 1}"] = str(output_path)
            tone_debug = image_state.metadata.get("aesthetic_tone_debug")
            debug_fields[f"debug:aesthetic_tone_applied:{image_index + 1}"] = str(
                bool(image_state.metadata.get("aesthetic_tone_target_applied"))
            ).lower()
            if isinstance(tone_debug, dict):
                debug_fields[f"debug:aesthetic_current_tone:{image_index + 1}"] = (
                    _json_debug_value(tone_debug.get("current_tone", {}))
                )
                debug_fields[f"debug:aesthetic_target_tone:{image_index + 1}"] = (
                    _json_debug_value(tone_debug.get("target_tone", {}))
                )
                debug_fields[f"debug:aesthetic_tolerance:{image_index + 1}"] = (
                    _json_debug_value(
                        {
                            key: value.get("tolerance")
                            for key, value in tone_debug.get("target_tone", {}).items()
                            if isinstance(value, dict)
                        }
                    )
                )
                debug_fields[f"debug:aesthetic_tone_gap:{image_index + 1}"] = (
                    _json_debug_value(tone_debug.get("gap_by_metric", {}))
                )
                debug_fields[f"debug:aesthetic_tone_skip:{image_index + 1}"] = (
                    _json_debug_value(tone_debug.get("skip_by_metric", {}))
                )
                debug_fields[f"debug:aesthetic_applied_params:{image_index + 1}"] = (
                    _json_debug_value(tone_debug.get("applied_params", {}))
                )
            if image_state.fallback_to_original:
                debug_fields[f"debug:image_fallback:{image_index + 1}"] = "true"
                if image_state.failure_reason:
                    debug_fields[f"debug:image_failure:{image_index + 1}"] = (
                        image_state.failure_reason
                    )
            logger.info(
                "Completed final edit image processing.",
                extra=build_log_extra(
                    "final_edit.image.completed",
                    component="final_edit",
                    stage="image",
                    session_id=session_id,
                    final_index=image_index + 1,
                    image_index=image_index,
                    planned_tool_count=len(plan.tools),
                    executed_tool_count=len(image_state.executed_tools),
                    executed_tools=image_state.executed_tools,
                    used_fallback=image_state.fallback_to_original,
                    failure_reason=image_state.failure_reason,
                    input_path=str(draft_path),
                    output_path=str(output_path),
                    output_source=output_source,
                ),
            )
            edited_paths.append(output_path)
        return edited_paths

    async def _upload_edited_images(
        self,
        session_id: str,
        drafts: list[str],
        downloaded_drafts: list[Path],
        edited_paths: list[Path],
        debug_fields: dict[str, str],
        uploaded_results: list[str],
    ) -> None:
        for final_index, draft_key in enumerate(drafts, start=1):
            output_path = edited_paths[final_index - 1]
            draft_path = downloaded_drafts[final_index - 1]
            upload_source_kind = _determine_output_source(output_path, draft_path)
            upload_source_exists = output_path.exists()
            upload_width, upload_height = _read_image_dimensions(output_path)
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
                    upload_source_path=str(output_path),
                    upload_source_kind=upload_source_kind,
                    upload_source_exists=upload_source_exists,
                    upload_image_width=upload_width,
                    upload_image_height=upload_height,
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
                    upload_source_path=str(output_path),
                    upload_source_kind=upload_source_kind,
                    upload_source_exists=upload_source_exists,
                    upload_image_width=upload_width,
                    upload_image_height=upload_height,
                    elapsed_ms=int((time.perf_counter() - upload_started_at) * 1000),
                ),
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
        context = context or FinalEditSessionContext(caption="", keywords=[])
        debug_fields = self._build_debug_fields(session_dir, drafts, context)

        try:
            if not self.downloader.is_configured or not self.uploader.is_configured:
                return self._s3_failure_result(session_id, drafts, debug_fields)

            downloaded_drafts = await self._download_drafts(
                session_id,
                drafts,
                session_dir,
                debug_fields,
            )
            planner_fallback, plans_by_index = await self._plan_images(
                session_id,
                context,
                downloaded_drafts,
                debug_fields,
            )

            edited_paths = await self._process_images(
                session_id,
                session_dir,
                downloaded_drafts,
                plans_by_index,
                planner_fallback,
                context,
                debug_fields,
            )
            await self._upload_edited_images(
                session_id,
                drafts,
                downloaded_drafts,
                edited_paths,
                debug_fields,
                uploaded_results,
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
                tool_order=state.metadata.get("current_tool_order"),
                tool_params=state.metadata.get("current_tool_params"),
                input_shape=state.metadata.get("current_tool_input_shape"),
                output_shape=state.metadata.get("current_tool_output_shape")
                if phase == "completed"
                else None,
                used_fallback=state.fallback_to_original if phase == "failed" else None,
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
        reason = getattr(request.app.state, "final_edit_unavailable_reason", None)
        if reason:
            raise FinalEditUnavailableError(reason)
        raise FinalEditUnavailableError("Final edit service is not initialized.")
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
