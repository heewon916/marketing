from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import LlamaModelClientSettings, settings
from app.services.final_edit_tools import (
    AESTHETIC_TARGET_TONE_PROFILE,
    SUPPORTED_TOOL_SPECS,
    ToolName,
    supported_tool_names,
)
from app.services.remote_model_client import RemoteModelClient
from app.services.sessions import session_key

_JSON_ARRAY_PATTERN = re.compile(r"\[[\s\S]*\]")
DEFAULT_OWNER_PERSONA = "aesthetic"
PERSONA_TARGET_PRESETS: dict[str, dict[str, Any]] = {
    "friendly": {
        "contrast": -8,
        "highlights": -6,
        "shadows": 18,
        "vibrance": 10,
        "saturation": 8,
        "temperature": "warm",
        "tone_curve_shadow_lift": 8,
    },
    "professional": {
        "contrast": 12,
        "highlights": -10,
        "shadows": 8,
        "vibrance": -6,
        "saturation": -8,
        "temperature": "cool",
        "tone_curve_shadow_lift": 4,
    },
    "trendy": {
        "contrast": 18,
        "highlights": -16,
        "shadows": 10,
        "vibrance": 14,
        "saturation": 10,
        "temperature": "warm",
        "tone_curve_shadow_lift": 2,
    },
    "other": {
        "contrast": 0,
        "highlights": -8,
        "shadows": 10,
        "vibrance": -4,
        "saturation": -2,
        "temperature": "warm",
        "tone_curve_shadow_lift": 6,
    },
}
TARGET_PROFILE_KIND_TONE = "tone_profile"
TARGET_PROFILE_KIND_PRESET = "style_preset"
_TOOL_ORDER_GROUPS: dict[ToolName, int] = {
    "denoise": 0,
    "color_grading": 1,
    "sharpen": 1,
    "background_blur": 1,
    "upscale": 2,
}


@dataclass(frozen=True)
class FinalEditSessionContext:
    owner_persona: str = "aesthetic"
    caption: str = ""
    keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ImageEditPlan:
    image_index: int
    content: str
    strategy: str
    tools: list[ToolName]
    params: dict[str, dict[str, Any]]


class FinalEditPlanningError(RuntimeError):
    """Raised when the final-edit planner cannot build a usable plan."""


def build_upscale_only_plan(
    image_index: int,
    *,
    owner_persona: str = DEFAULT_OWNER_PERSONA,
    content: str = "draft image",
    strategy: str = "Apply minimum color grading before mandatory Real-ESRGAN upscale.",
) -> ImageEditPlan:
    resolved_persona, resolved_target, _used_fallback, target_kind = (
        resolve_owner_persona_target(owner_persona)
    )
    color_grading_params = (
        {}
        if target_kind == TARGET_PROFILE_KIND_TONE
        else dict(resolved_target)
    )
    return ImageEditPlan(
        image_index=image_index,
        content=content,
        strategy=strategy,
        tools=["color_grading", "upscale"],
        params={
            "color_grading": color_grading_params,
            "upscale": {"scale": 2},
        },
    )


def normalize_image_edit_plan(plan: ImageEditPlan) -> ImageEditPlan:
    seen_tools: set[ToolName] = set()
    deduplicated_tools: list[ToolName] = []
    for tool_name in plan.tools:
        if tool_name in seen_tools:
            continue
        deduplicated_tools.append(tool_name)
        seen_tools.add(tool_name)

    if "upscale" not in seen_tools:
        deduplicated_tools.append("upscale")
        seen_tools.add("upscale")

    indexed_tools = list(enumerate(deduplicated_tools))
    ordered_tools = [
        tool_name
        for _, tool_name in sorted(
            indexed_tools,
            key=lambda item: (
                _TOOL_ORDER_GROUPS[item[1]],
                item[0],
            ),
        )
    ]
    normalized_params: dict[str, dict[str, Any]] = {}
    for tool_name in ordered_tools:
        if tool_name == "upscale":
            normalized_params[tool_name] = {"scale": 2}
            continue
        normalized_params[tool_name] = dict(plan.params.get(tool_name, {}))

    return ImageEditPlan(
        image_index=plan.image_index,
        content=plan.content,
        strategy=plan.strategy,
        tools=ordered_tools,
        params=normalized_params,
    )


def _normalize_redis_value(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if value is None:
        return ""
    return str(value)


def _sorted_prefixed_values(payload: dict[str, object], prefix: str) -> list[str]:
    indexed_values: list[tuple[int, str]] = []
    for key, value in payload.items():
        normalized_key = _normalize_redis_value(key)
        if not normalized_key.startswith(prefix):
            continue
        suffix = normalized_key.removeprefix(prefix)
        try:
            index = int(suffix)
        except ValueError:
            continue
        normalized_value = _normalize_redis_value(value).strip()
        if normalized_value:
            indexed_values.append((index, normalized_value))
    indexed_values.sort(key=lambda item: item[0])
    return [value for _, value in indexed_values]


def _humanize_final_keyword(value: str) -> str:
    _, separator, display_name = value.partition(":")
    if separator and display_name.strip():
        return display_name.strip()
    return value.strip()


def resolve_owner_persona_preset(
    owner_persona: str,
) -> tuple[str, dict[str, Any], bool]:
    resolved_persona, resolved_target, used_fallback, _target_kind = (
        resolve_owner_persona_target(owner_persona)
    )
    return resolved_persona, resolved_target, used_fallback


def resolve_owner_persona_target(
    owner_persona: str,
) -> tuple[str, dict[str, Any], bool, str]:
    normalized_owner_persona = owner_persona.strip().lower()
    if normalized_owner_persona == DEFAULT_OWNER_PERSONA:
        return (
            DEFAULT_OWNER_PERSONA,
            dict(AESTHETIC_TARGET_TONE_PROFILE),
            False,
            TARGET_PROFILE_KIND_TONE,
        )
    preset = PERSONA_TARGET_PRESETS.get(normalized_owner_persona)
    if preset is not None:
        return normalized_owner_persona, dict(preset), False, TARGET_PROFILE_KIND_PRESET
    return (
        DEFAULT_OWNER_PERSONA,
        dict(AESTHETIC_TARGET_TONE_PROFILE),
        True,
        TARGET_PROFILE_KIND_TONE,
    )


async def load_final_edit_session_context(
    redis: Redis,
    session_id: str,
) -> FinalEditSessionContext:
    payload = await redis.hgetall(session_key(session_id))
    normalized_payload = {
        _normalize_redis_value(key): _normalize_redis_value(value)
        for key, value in payload.items()
    }
    owner_persona = normalized_payload.get("owner_persona", "").strip().lower()
    if not owner_persona:
        owner_persona = DEFAULT_OWNER_PERSONA
    caption = normalized_payload.get("caption", "").strip()
    keywords = _sorted_prefixed_values(normalized_payload, "draft_keyword:")
    if not keywords:
        keywords = [
            _humanize_final_keyword(value)
            for value in _sorted_prefixed_values(normalized_payload, "final_keyword:")
        ]
    return FinalEditSessionContext(
        owner_persona=owner_persona,
        caption=caption,
        keywords=keywords,
    )


def _tool_catalog_text() -> str:
    lines = ["[supported tools]"]
    for index, spec in enumerate(SUPPORTED_TOOL_SPECS, start=1):
        lines.append(f"{index}. {spec.name} - {spec.description}")
        params_text = ", ".join(
            f"{key}: {value}" for key, value in spec.params_schema.items()
        )
        lines.append(f"   params: {{{params_text}}}")
    return "\n".join(lines)


def _target_preset_text(context: FinalEditSessionContext) -> str:
    preset_persona, preset, preset_fallback, target_kind = resolve_owner_persona_target(
        context.owner_persona
    )
    preset_json = json.dumps(preset, ensure_ascii=False)
    return (
        f"[owner_persona] {context.owner_persona or DEFAULT_OWNER_PERSONA}\n"
        f"[target_preset_persona] {preset_persona}\n"
        f"[target_preset_fallback] {'true' if preset_fallback else 'false'}\n"
        f"[target_profile_kind] {target_kind}\n"
        f"[target_preset] {preset_json}"
    )


def _few_shot_example() -> str:
    return """
Example output:
[
  {
    "image_index": 0,
    "content": "A signature cake placed on a bright cafe table.",
    "strategy": "The image is brighter and more saturated than the target aesthetic preset, so denoise first, gently lower highlights, mute color, lift shadows only enough to approach the preset, and upscale last.",
    "tools": ["denoise", "color_grading", "sharpen", "upscale"],
    "params": {
      "denoise": {"strength": 0.5},
      "color_grading": {
        "contrast": -10,
        "highlights": -14,
        "shadows": 12,
        "vibrance": -18,
        "saturation": -12,
        "temperature": "cool",
        "tone_curve_shadow_lift": 8
      },
      "sharpen": {"strength": 0.35},
      "upscale": {"scale": 2}
    }
  }
]
""".strip()


def build_final_edit_prompt(
    context: FinalEditSessionContext,
    image_count: int,
) -> str:
    keywords_text = ", ".join(context.keywords) if context.keywords else "(none)"
    caption_text = context.caption or "(none)"
    return (
        "You are a photo editing planner for draft images.\n\n"
        f"{_tool_catalog_text()}\n\n"
        f"{_target_preset_text(context)}\n"
        f"[caption] {caption_text}\n"
        f"[keywords] {keywords_text}\n\n"
        "[instructions]\n"
        f"1. You must create an edit plan for all {image_count} input images.\n"
        f"2. The JSON array must include every image_index from 0 to {image_count - 1} exactly once.\n"
        "3. Analyze each image's current style and compare it against the target preset for the owner persona.\n"
        "4. Use only supported tools.\n"
        "5. Do not copy the target preset blindly. Estimate the gap between the current image and the target tone, then apply only the minimum adjustment needed for that image.\n"
        "6. Summarize the gap analysis briefly in strategy.\n"
        "7. If owner_persona is aesthetic, use the target_preset as a tone profile with target and tolerance values, and reason about the current image's gap from those metrics.\n"
        "8. If color_grading is used, fill contrast, highlights, shadows, vibrance, saturation, temperature, and tone_curve_shadow_lift explicitly.\n"
        "9. The output params should represent the per-image adjustment needed to move toward the preset, not the preset value itself.\n"
        "10. If denoise is used, it must appear before any filter tool.\n"
        "11. Upscale must be included for every image, it is 2x only, and it must appear after every filter tool.\n"
        "12. Do not place upscale on an image unless at least one filter tool precedes it.\n"
        "13. Denoise alone is not enough to justify upscale; insert a filter before upscale.\n"
        "14. Treat color_grading, sharpen, and background_blur as filter tools for ordering.\n"
        "15. Output only a JSON array.\n\n"
        f"{_few_shot_example()}"
    )


def image_path_to_data_uri(image_path: str) -> str:
    data = Path(image_path).read_bytes()
    encoded = base64.b64encode(data).decode("utf-8")
    suffix = Path(image_path).suffix.lower()
    media_type = "image/png" if suffix == ".png" else "image/jpeg"
    return f"data:{media_type};base64,{encoded}"


def _extract_json_array(raw_output: str) -> str:
    cleaned = raw_output.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
    if cleaned.endswith("```"):
        cleaned = cleaned.rsplit("```", 1)[0]
    cleaned = cleaned.strip()

    if cleaned.startswith("[") and cleaned.endswith("]"):
        return cleaned

    match = _JSON_ARRAY_PATTERN.search(cleaned)
    if match is None:
        raise FinalEditPlanningError("Planner did not return a JSON array.")
    return match.group(0)


def parse_image_edit_plans(raw_output: str) -> list[ImageEditPlan]:
    try:
        payload = json.loads(_extract_json_array(raw_output))
    except json.JSONDecodeError as exc:
        raise FinalEditPlanningError("Planner returned invalid JSON.") from exc

    if not isinstance(payload, list):
        raise FinalEditPlanningError("Planner payload must be a list.")

    allowed_tools = set(supported_tool_names())
    seen_indexes: set[int] = set()
    plans: list[ImageEditPlan] = []

    for item in payload:
        if not isinstance(item, dict):
            raise FinalEditPlanningError("Planner payload must contain objects only.")

        required_fields = {"image_index", "content", "strategy", "tools", "params"}
        missing_fields = required_fields - set(item.keys())
        if missing_fields:
            raise FinalEditPlanningError(
                f"Planner payload is missing fields: {sorted(missing_fields)}"
            )

        image_index = item["image_index"]
        if not isinstance(image_index, int):
            raise FinalEditPlanningError("image_index must be an integer.")
        if image_index in seen_indexes:
            raise FinalEditPlanningError("image_index values must be unique.")
        seen_indexes.add(image_index)

        tools = item["tools"]
        if not isinstance(tools, list) or not tools:
            raise FinalEditPlanningError("tools must be a non-empty list.")

        normalized_tools: list[ToolName] = []
        for tool_name in tools:
            if not isinstance(tool_name, str) or tool_name not in allowed_tools:
                raise FinalEditPlanningError(f"Unsupported tool requested: {tool_name}")
            normalized_tools.append(tool_name)

        params = item["params"]
        if not isinstance(params, dict):
            raise FinalEditPlanningError("params must be an object.")
        normalized_params: dict[str, dict[str, Any]] = {}
        for tool_name in normalized_tools:
            tool_params = params.get(tool_name, {})
            if not isinstance(tool_params, dict):
                raise FinalEditPlanningError(
                    f"params for tool '{tool_name}' must be an object."
                )
            normalized_params[tool_name] = tool_params

        content = str(item["content"]).strip()
        strategy = str(item["strategy"]).strip()
        if not content or not strategy:
            raise FinalEditPlanningError("content and strategy must be non-empty.")

        plans.append(
            normalize_image_edit_plan(
                ImageEditPlan(
                    image_index=image_index,
                    content=content,
                    strategy=strategy,
                    tools=normalized_tools,
                    params=normalized_params,
                )
            )
        )

    return plans


class FinalEditPlannerClient:
    """Client for requesting image edit plans from an OpenAI-compatible VLM."""

    def __init__(
        self,
        model_settings: LlamaModelClientSettings,
        model_name: str,
    ) -> None:
        self.model_settings = model_settings
        self.model_name = model_name
        self._remote_client = RemoteModelClient(
            base_url=self.model_settings.base_url,
            chat_endpoint=self.model_settings.chat_endpoint,
            health_endpoint=self.model_settings.health_endpoint,
            api_key=self.model_settings.api_key,
            timeout_seconds=self.model_settings.timeout_seconds,
        )
        self._health_checked = False
        self.last_raw_output: str | None = None

    async def preload(self) -> None:
        await self._check_server_connection()

    async def build_plans(
        self,
        image_paths: list[str],
        context: FinalEditSessionContext,
    ) -> list[ImageEditPlan]:
        if not self.model_settings.enabled:
            raise FinalEditPlanningError("Final-edit planner is disabled.")
        if not image_paths:
            raise FinalEditPlanningError("No image paths were provided to the planner.")

        raw_output = await self._request_plan(image_paths, context)
        self.last_raw_output = raw_output
        plans = parse_image_edit_plans(raw_output)
        if len(plans) > len(image_paths):
            raise FinalEditPlanningError("Planner returned too many image plans.")
        for plan in plans:
            if plan.image_index < 0 or plan.image_index >= len(image_paths):
                raise FinalEditPlanningError("Planner returned an out-of-range image_index.")
        return plans

    async def _request_plan(
        self,
        image_paths: list[str],
        context: FinalEditSessionContext,
    ) -> str:
        content = [
            {"type": "image_url", "image_url": {"url": image_path_to_data_uri(path)}}
            for path in image_paths
        ]
        content.append(
            {
                "type": "text",
                "text": build_final_edit_prompt(context, len(image_paths)),
            }
        )
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": content}],
            "temperature": self.model_settings.temperature,
            "top_p": self.model_settings.top_p,
            "max_tokens": self.model_settings.max_tokens,
        }
        response = await self._remote_client.post_chat_completion(payload)
        response.raise_for_status()
        raw_output = self._remote_client.extract_message_content(response)
        if not isinstance(raw_output, str) or not raw_output.strip():
            raise FinalEditPlanningError("Planner returned an empty response.")
        return raw_output

    async def _check_server_connection(self) -> None:
        if not self.model_settings.base_url:
            raise FinalEditPlanningError("Final-edit planner base URL is not configured.")
        await self._remote_client.check_health()
        self._health_checked = True


def build_final_edit_planner_client() -> FinalEditPlannerClient:
    return FinalEditPlannerClient(
        model_settings=settings.final_edit_model_client,
        model_name=settings.FINAL_EDIT_MODEL_NAME,
    )


def get_final_edit_planner_client(request: Request) -> FinalEditPlannerClient:
    service = getattr(request.app.state, "final_edit_planner_client", None)
    if service is None:
        raise RuntimeError("Final edit planner client is not initialized.")
    return service
