from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fastapi import Request
import httpx
from openai import AsyncOpenAI
from redis.asyncio import Redis

from app.core.config import LlamaModelClientSettings, settings
from app.services.final_edit_tools import SUPPORTED_TOOL_SPECS, ToolName, supported_tool_names
from app.services.sessions import session_key

_JSON_ARRAY_PATTERN = re.compile(r"\[[\s\S]*\]")


@dataclass(frozen=True)
class FinalEditSessionContext:
    caption: str
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


async def load_final_edit_session_context(
    redis: Redis,
    session_id: str,
) -> FinalEditSessionContext:
    payload = await redis.hgetall(session_key(session_id))
    normalized_payload = {
        _normalize_redis_value(key): _normalize_redis_value(value)
        for key, value in payload.items()
    }
    caption = normalized_payload.get("caption", "").strip()
    keywords = _sorted_prefixed_values(normalized_payload, "draft_keyword:")
    if not keywords:
        keywords = [
            _humanize_final_keyword(value)
            for value in _sorted_prefixed_values(normalized_payload, "final_keyword:")
        ]
    return FinalEditSessionContext(caption=caption, keywords=keywords)


def _tool_catalog_text() -> str:
    lines = ["사용 가능한 편집 도구 목록:"]
    for index, spec in enumerate(SUPPORTED_TOOL_SPECS, start=1):
        lines.append(f"{index}. {spec.name} - {spec.description}")
        params_text = ", ".join(
            f"{key}: {value}" for key, value in spec.params_schema.items()
        )
        lines.append(f"   params: {{{params_text}}}")
    return "\n".join(lines)


def _few_shot_example() -> str:
    return """
출력 예시:
[
  {
    "image_index": 0,
    "content": "어두운 실내 테이블과 디저트가 함께 보인다.",
    "strategy": "노이즈를 줄이고 따뜻한 톤으로 정리한 뒤 디테일을 살린다.",
    "tools": ["denoise", "color_grading", "sharpen"],
    "params": {
      "denoise": {"strength": 0.5},
      "color_grading": {"temperature": "warm", "saturation": 0.15, "brightness": 0.1},
      "sharpen": {"strength": 0.35}
    }
  }
]
""".strip()


def build_final_edit_prompt(context: FinalEditSessionContext) -> str:
    keywords_text = ", ".join(context.keywords) if context.keywords else "(없음)"
    caption_text = context.caption or "(없음)"
    return (
        "너는 음식점 홍보 이미지를 다듬는 사진 편집 전략가다.\n\n"
        f"{_tool_catalog_text()}\n\n"
        f"[캡션] {caption_text}\n"
        f"[키워드] {keywords_text}\n\n"
        "[지침]\n"
        "1. 각 이미지의 내용과 캡션 분위기를 함께 고려한다.\n"
        "2. 지원된 도구만 사용한다.\n"
        "3. 각 도구의 params에는 구체적인 값을 넣는다.\n"
        "4. 결과는 이미지별 JSON 배열만 출력한다.\n\n"
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
            ImageEditPlan(
                image_index=image_index,
                content=content,
                strategy=strategy,
                tools=normalized_tools,
                params=normalized_params,
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
        self._health_checked = False

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
        client = AsyncOpenAI(
            base_url=self.model_settings.base_url,
            api_key=self.model_settings.api_key or "dummy",
            timeout=self.model_settings.timeout_seconds,
        )
        content = [
            {"type": "image_url", "image_url": {"url": image_path_to_data_uri(path)}}
            for path in image_paths
        ]
        content.append({"type": "text", "text": build_final_edit_prompt(context)})

        response = await client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": content}],
            temperature=self.model_settings.temperature,
            top_p=self.model_settings.top_p,
            max_tokens=self.model_settings.max_tokens,
        )
        message = response.choices[0].message
        raw_output = message.content or ""
        if not isinstance(raw_output, str) or not raw_output.strip():
            raise FinalEditPlanningError("Planner returned an empty response.")
        return raw_output

    async def _check_server_connection(self) -> None:
        if not self.model_settings.base_url:
            raise FinalEditPlanningError("Final-edit planner base URL is not configured.")
        async with httpx.AsyncClient(timeout=self.model_settings.timeout_seconds) as client:
            response = await client.get(
                f"{self.model_settings.base_url}{self.model_settings.health_endpoint}"
            )
            response.raise_for_status()
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
