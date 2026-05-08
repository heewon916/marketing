from __future__ import annotations

from dataclasses import dataclass, field
import json
import logging
import re
import time
from typing import Any

from fastapi import Request
import httpx

from app.core.config import settings
from app.logging import build_log_extra, preview_text
from app.services.content_purpose import ContentPurpose
from app.services.weather_tags import (
    PRECIP_CLEAR,
    PRECIP_CLOUDY,
    PRECIP_HEAVY_RAIN,
    PRECIP_RAIN,
    SPECIAL_FINE_DUST,
    SPECIAL_SEASONAL_CHANGE,
    SPECIAL_TYPHOON,
    TEMP_COLD,
    TEMP_FREEZING,
    TEMP_HOT,
    TEMP_MILD,
    TEMP_SCORCHING,
)

logger = logging.getLogger(__name__)

_MENU_PROMOTION_PROMPT_TEMPLATE = """You generate short Korean Instagram marketing copy for a small shop owner.

Rules:
- Return JSON object text only.
- Use this schema: {{"guide_text": "...", "caption": "...", "hashtags": ["#..."]}}.
- The post purpose is "메뉴 홍보".
- "guide_text" should be 1 to 2 Korean sentences telling the owner what to emphasize in the photo.
- "caption" should be a warm Korean Instagram caption of 1 to 3 short sentences.
- "hashtags" should contain 1 to 5 concise hashtags including the leading # symbol.
- Use the provided keywords naturally. Do not invent unrelated products.
- Frame the copy like a menu, product, ingredient, or store offering promotion.
- Keep the output suitable for an Instagram post by a local store owner.

Input:
- owner_persona: {owner_persona}
- weather_context: {weather_context}
- keywords: {keywords}
"""

_BUSINESS_NOTICE_PROMPT_TEMPLATE = """You generate short Korean Instagram marketing copy for a small shop owner.

Rules:
- Return JSON object text only.
- Use this schema: {{"guide_text": "...", "caption": "...", "hashtags": ["#..."]}}.
- The post purpose is "영업 공지".
- "guide_text" should be 1 to 2 Korean sentences telling the owner what to emphasize in the photo.
- "caption" should be a warm Korean Instagram caption of 1 to 3 short sentences.
- "hashtags" should contain 1 to 5 concise hashtags including the leading # symbol.
- Use the provided keywords naturally. Do not invent unrelated products.
- Frame the copy like a clear business notice about operation, schedule, or availability.
- Keep the output suitable for an Instagram post by a local store owner.

Input:
- owner_persona: {owner_persona}
- weather_context: {weather_context}
- keywords: {keywords}
"""

_DAILY_SHARE_PROMPT_TEMPLATE = """You generate short Korean Instagram marketing copy for a small shop owner.

Rules:
- Return JSON object text only.
- Use this schema: {{"guide_text": "...", "caption": "...", "hashtags": ["#..."]}}.
- The post purpose is "일상 공유".
- "guide_text" should be 1 to 2 Korean sentences telling the owner what to emphasize in the photo.
- "caption" should be a warm Korean Instagram caption of 1 to 3 short sentences.
- "hashtags" should contain 1 to 5 concise hashtags including the leading # symbol.
- Use the provided keywords naturally. Do not invent unrelated products.
- Frame the copy like a daily share about the owner's routine, store atmosphere, or behind-the-scenes moment.
- Keep the output suitable for an Instagram post by a local store owner.

Input:
- owner_persona: {owner_persona}
- weather_context: {weather_context}
- keywords: {keywords}
"""

DEFAULT_FALLBACK_GUIDE_TEXT = (
    "Capture the store atmosphere clearly so the main subject stands out."
)

_PRIMARY_WEATHER_TAG_PRIORITY = (
    PRECIP_HEAVY_RAIN,
    PRECIP_RAIN,
    PRECIP_CLEAR,
    PRECIP_CLOUDY,
)

_SECONDARY_WEATHER_TAG_PRIORITY = (
    SPECIAL_TYPHOON,
    SPECIAL_FINE_DUST,
    SPECIAL_SEASONAL_CHANGE,
    TEMP_SCORCHING,
    TEMP_HOT,
    TEMP_COLD,
    TEMP_FREEZING,
    TEMP_MILD,
)

_WEATHER_CONTEXT_BY_TAG = {
    PRECIP_HEAVY_RAIN: "폭우가 오는 날",
    PRECIP_RAIN: "비 오는 날",
    PRECIP_CLEAR: "맑은 날",
    PRECIP_CLOUDY: "흐린 날",
    SPECIAL_TYPHOON: "강풍 주의가 있는 날",
    SPECIAL_FINE_DUST: "미세먼지 주의가 있는 날",
    SPECIAL_SEASONAL_CHANGE: "환절기",
    TEMP_SCORCHING: "무더운 날",
    TEMP_HOT: "더운 날",
    TEMP_COLD: "쌀쌀한 날",
    TEMP_FREEZING: "매우 추운 날",
    TEMP_MILD: "선선한 날",
}

_WEATHER_HASHTAG_BY_TAG = {
    PRECIP_HEAVY_RAIN: "#폭우",
    PRECIP_RAIN: "#비오는날",
    PRECIP_CLEAR: "#맑은날",
    PRECIP_CLOUDY: "#흐린날",
    SPECIAL_TYPHOON: "#강풍주의",
    SPECIAL_FINE_DUST: "#미세먼지주의",
    SPECIAL_SEASONAL_CHANGE: "#환절기",
    TEMP_SCORCHING: "#무더위",
    TEMP_HOT: "#더운날",
    TEMP_COLD: "#쌀쌀한날",
    TEMP_FREEZING: "#한파",
    TEMP_MILD: "#선선한날",
}


def _select_weather_copy_tags(weather_tags: list[str]) -> list[str]:
    selected: list[str] = []

    for tag in _PRIMARY_WEATHER_TAG_PRIORITY:
        if tag in weather_tags:
            selected.append(tag)
            break

    for tag in _SECONDARY_WEATHER_TAG_PRIORITY:
        if tag in weather_tags and tag not in selected:
            selected.append(tag)
            break

    if not selected:
        for tag in weather_tags:
            if tag in _WEATHER_CONTEXT_BY_TAG and tag not in selected:
                selected.append(tag)
            if len(selected) == 2:
                break

    return selected


def _build_weather_context(weather_tags: list[str]) -> str:
    selected_tags = _select_weather_copy_tags(weather_tags)
    if not selected_tags:
        return "특별한 날씨 포인트 없음"
    return ", ".join(_WEATHER_CONTEXT_BY_TAG[tag] for tag in selected_tags)


def _build_weather_hashtags(weather_tags: list[str], limit: int = 2) -> list[str]:
    hashtags: list[str] = []
    for tag in _select_weather_copy_tags(weather_tags):
        hashtag = _WEATHER_HASHTAG_BY_TAG.get(tag)
        if hashtag is None or hashtag in hashtags:
            continue
        hashtags.append(hashtag)
        if len(hashtags) == limit:
            break
    return hashtags


class CaptionGenerationUnavailableError(RuntimeError):
    """Raised when caption generation is unavailable."""


@dataclass
class CaptionGenerationResult:
    guide_text: str
    draft_caption: str
    draft_hashtags: list[str] = field(default_factory=list)

    @property
    def stored_caption(self) -> str:
        return " ".join(
            part for part in [self.draft_caption, *self.draft_hashtags] if part
        )


@dataclass
class CaptionGenerationRequest:
    purpose: ContentPurpose
    keywords: list[str]
    owner_persona: str
    weather_tags: list[str] = field(default_factory=list)


@dataclass
class CaptionFallbackResult:
    result: CaptionGenerationResult
    fallback_source: str | None


class CaptionPipeline:
    def __init__(self, purpose: ContentPurpose, prompt_template: str) -> None:
        self.purpose = purpose
        self.prompt_template = prompt_template

    def build_prompt(self, request: CaptionGenerationRequest) -> str:
        return self.prompt_template.format(
            owner_persona=request.owner_persona.strip(),
            weather_context=_build_weather_context(request.weather_tags),
            keywords=", ".join(request.keywords) if request.keywords else "none",
        )

    def build_fallback(
        self,
        request: CaptionGenerationRequest,
        fallback_source: str | None,
    ) -> CaptionFallbackResult:
        draft_caption, draft_hashtags = self._build_fallback_caption(request)
        guide_text = (
            self._build_fallback_guide_text(request)
            if request.keywords
            else DEFAULT_FALLBACK_GUIDE_TEXT
        )
        effective_fallback_source = fallback_source
        if not request.keywords and effective_fallback_source is None:
            effective_fallback_source = "default_guide"
        return CaptionFallbackResult(
            result=CaptionGenerationResult(
                guide_text=guide_text,
                draft_caption=draft_caption,
                draft_hashtags=draft_hashtags,
            ),
            fallback_source=effective_fallback_source,
        )

    def _build_fallback_caption(
        self,
        request: CaptionGenerationRequest,
    ) -> tuple[str, list[str]]:
        keyword_phrase = (
            ", ".join(request.keywords) if request.keywords else "today's highlights"
        )
        weather_context = _build_weather_context(request.weather_tags)
        if weather_context != "특별한 날씨 포인트 없음":
            caption = (
                f"{weather_context} 분위기와 {request.owner_persona} 무드로 "
                f"{keyword_phrase}를 소개해보세요."
            )
        else:
            caption = (
                f"{request.owner_persona} 무드로 {keyword_phrase}를 소개해보세요."
            )
        hashtags = [f"#{kw.replace(' ', '')}" for kw in request.keywords[:5]]
        hashtags.extend(
            hashtag for hashtag in _build_weather_hashtags(request.weather_tags)
            if hashtag not in hashtags
        )
        if not hashtags:
            hashtags.append("#오늘기록")
        return caption, hashtags

    def _build_fallback_guide_text(self, request: CaptionGenerationRequest) -> str:
        keyword_phrase = ", ".join(request.keywords)
        return (
            f"Make sure {keyword_phrase} is clearly visible in the shot. "
            "Check the framing and subject emphasis before shooting."
        )


def _build_caption_pipeline_registry() -> dict[ContentPurpose, CaptionPipeline]:
    return {
        "메뉴 홍보": CaptionPipeline("메뉴 홍보", _MENU_PROMOTION_PROMPT_TEMPLATE),
        "영업 공지": CaptionPipeline("영업 공지", _BUSINESS_NOTICE_PROMPT_TEMPLATE),
        "일상 공유": CaptionPipeline("일상 공유", _DAILY_SHARE_PROMPT_TEMPLATE),
    }


class CaptionGenerationService:
    def __init__(
        self,
        enabled: bool = True,
        max_tokens: int = 128,
        temperature: float = 0.7,
        top_p: float = 0.9,
        timeout_seconds: float = 30.0,
        base_url: str | None = None,
        chat_endpoint: str | None = None,
        health_endpoint: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.enabled = enabled
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.timeout_seconds = timeout_seconds
        self.base_url = (base_url or "").rstrip("/")
        self.chat_endpoint = chat_endpoint or "/v1/chat/completions"
        self.health_endpoint = health_endpoint or "/health"
        self.api_key = api_key
        self._server_checked = False
        self._pipelines = _build_caption_pipeline_registry()

    async def preload(self) -> None:
        await self._check_server_connection()

    async def generate_text(
        self,
        request: CaptionGenerationRequest,
    ) -> CaptionGenerationResult:
        if not self.enabled:
            raise CaptionGenerationUnavailableError(
                "Caption generation model is disabled."
            )

        prompt = self._get_pipeline(request.purpose).build_prompt(request)
        started_at = time.perf_counter()

        logger.info(
            "Caption generation inference started.",
            extra=build_log_extra(
                "caption_generation.inference.started",
                component="caption_generation",
                stage="inference",
                outcome="started",
                caption_timeout_seconds=self.timeout_seconds,
                caption_model_base_url=self.base_url,
                caption_chat_endpoint=self.chat_endpoint,
                caption_health_endpoint=self.health_endpoint,
                caption_keyword_count=len(request.keywords),
                caption_keywords_preview=", ".join(request.keywords[:3]),
                owner_persona=request.owner_persona,
                purpose=request.purpose,
            ),
        )

        try:
            raw_output = await self._generate(prompt, purpose=request.purpose)
        except TimeoutError as exc:
            raise CaptionGenerationUnavailableError(
                "Caption generation timed out."
            ) from exc
        except CaptionGenerationUnavailableError:
            raise
        except Exception as exc:
            raise CaptionGenerationUnavailableError(
                "Caption generation inference failed."
            ) from exc

        result = self._parse_generation_result(raw_output)
        logger.info(
            "Caption generation inference finished.",
            extra=build_log_extra(
                "caption_generation.inference.completed",
                component="caption_generation",
                stage="inference",
                outcome="succeeded",
                elapsed_ms=int((time.perf_counter() - started_at) * 1000),
                guide_text_length=len(result.guide_text),
                draft_caption_length=len(result.draft_caption),
                hashtag_count=len(result.draft_hashtags),
                purpose=request.purpose,
            ),
        )
        return result

    def build_fallback_result(
        self,
        request: CaptionGenerationRequest,
        fallback_source: str | None,
    ) -> CaptionFallbackResult:
        return self._get_pipeline(request.purpose).build_fallback(
            request,
            fallback_source,
        )

    def _build_request_payload(
        self,
        prompt: str,
        include_response_format: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only a JSON object with guide_text, caption, and hashtags."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }
        if include_response_format:
            payload["response_format"] = {
                "type": "json_object",
                "schema": {
                    "type": "object",
                    "properties": {
                        "guide_text": {"type": "string"},
                        "caption": {"type": "string"},
                        "hashtags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                            "maxItems": 5,
                        },
                    },
                    "required": ["guide_text", "caption", "hashtags"],
                },
            }
        return payload

    def _build_request_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    @property
    def _chat_url(self) -> str:
        return f"{self.base_url}{self.chat_endpoint}"

    @property
    def _health_url(self) -> str:
        return f"{self.base_url}{self.health_endpoint}"

    async def _post_chat_completion(
        self,
        prompt: str,
        *,
        include_response_format: bool,
    ) -> httpx.Response:
        payload = self._build_request_payload(prompt, include_response_format)
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            return await client.post(
                self._chat_url,
                headers=self._build_request_headers(),
                json=payload,
            )

    async def _check_server_connection(self) -> None:
        if not self.base_url:
            raise CaptionGenerationUnavailableError(
                "Caption generation server base URL is not configured."
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self._health_url)
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise CaptionGenerationUnavailableError(
                "Caption generation server connectivity check timed out."
            ) from exc
        except httpx.HTTPStatusError as exc:
            raise CaptionGenerationUnavailableError(
                "Caption generation server connectivity check returned "
                f"HTTP {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise CaptionGenerationUnavailableError(
                "Caption generation server connectivity check failed."
            ) from exc

        self._server_checked = True
        logger.info(
            "Caption generation server connectivity check completed.",
            extra=build_log_extra(
                "caption_generation.server_check.completed",
                component="caption_generation",
                stage="server_check",
                outcome="succeeded",
                caption_model_base_url=self.base_url,
                caption_health_endpoint=self.health_endpoint,
                caption_http_status=response.status_code,
            ),
        )

    @staticmethod
    def _is_response_format_unsupported(response: httpx.Response) -> bool:
        if response.status_code < 400:
            return False
        body = response.text.lower()
        return "response_format" in body or "json_object" in body or "schema" in body

    def _get_pipeline(self, purpose: ContentPurpose) -> CaptionPipeline:
        pipeline = self._pipelines.get(purpose)
        if pipeline is None:
            raise CaptionGenerationUnavailableError(
                f"Caption pipeline is not configured for purpose: {purpose}."
            )
        return pipeline

    async def _generate(self, prompt: str, *, purpose: ContentPurpose) -> str:
        if not self.base_url:
            raise CaptionGenerationUnavailableError(
                "Caption generation server base URL is not configured."
            )

        response: httpx.Response | None = None
        try:
            response = await self._post_chat_completion(
                prompt,
                include_response_format=True,
            )
            if self._is_response_format_unsupported(response):
                response = await self._post_chat_completion(
                    prompt,
                    include_response_format=False,
                )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError from exc
        except httpx.HTTPStatusError as exc:
            raise CaptionGenerationUnavailableError(
                f"Caption generation server returned HTTP {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise CaptionGenerationUnavailableError(
                "Caption generation server request failed."
            ) from exc

        self._server_checked = True
        response_payload = response.json()
        raw_output = (
            response_payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        logger.info(
            "llama-server caption completion returned.",
            extra=build_log_extra(
                "caption_generation.generate.completed",
                component="caption_generation",
                stage="generate",
                outcome="succeeded",
                purpose=purpose,
                caption_model_base_url=self.base_url,
                caption_chat_endpoint=self.chat_endpoint,
                caption_http_status=response.status_code if response is not None else None,
                raw_output_preview=preview_text(
                    raw_output,
                    settings.LOG_EVENT_PREVIEW_MAX_LEN,
                ),
            ),
        )
        return raw_output

    @staticmethod
    def _extract_json_payload(raw_output: str) -> str:
        match = re.search(r"\{[\s\S]*\}", raw_output)
        if match is None:
            raise CaptionGenerationUnavailableError(
                "Caption generation did not return JSON."
            )
        return match.group(0)

    def _parse_generation_result(self, raw_output: str) -> CaptionGenerationResult:
        try:
            payload = json.loads(self._extract_json_payload(raw_output))
        except json.JSONDecodeError as exc:
            raise CaptionGenerationUnavailableError(
                "Caption generation returned invalid JSON."
            ) from exc

        if not isinstance(payload, dict):
            raise CaptionGenerationUnavailableError(
                "Caption generation returned a non-object payload."
            )

        guide_text = self._normalize_text(payload.get("guide_text"))
        draft_caption = self._normalize_text(payload.get("caption"))
        draft_hashtags = self._normalize_hashtags(payload.get("hashtags"))

        if not guide_text or not draft_caption or not draft_hashtags:
            raise CaptionGenerationUnavailableError(
                "Caption generation returned incomplete text fields."
            )

        return CaptionGenerationResult(
            guide_text=guide_text,
            draft_caption=draft_caption,
            draft_hashtags=draft_hashtags,
        )

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return re.sub(r"\s+", " ", value.strip())

    @staticmethod
    def _normalize_hashtags(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []

        normalized: list[str] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, str):
                continue
            hashtag = re.sub(r"\s+", "", item.strip())
            if not hashtag:
                continue
            if not hashtag.startswith("#"):
                hashtag = f"#{hashtag.lstrip('#')}"
            if len(hashtag) < 2 or hashtag in seen:
                continue
            seen.add(hashtag)
            normalized.append(hashtag)
            if len(normalized) == 5:
                break
        return normalized


def build_caption_generation_service() -> CaptionGenerationService:
    client = settings.caption_model_client
    return CaptionGenerationService(
        enabled=client.enabled,
        max_tokens=client.max_tokens,
        temperature=client.temperature,
        top_p=client.top_p,
        timeout_seconds=client.timeout_seconds,
        base_url=client.base_url,
        chat_endpoint=client.chat_endpoint,
        health_endpoint=client.health_endpoint,
        api_key=client.api_key,
    )


def get_caption_generation_service(request: Request) -> CaptionGenerationService:
    service = getattr(request.app.state, "caption_generation_service", None)
    if service is None:
        raise RuntimeError("Caption generation service is not initialized.")
    return service
