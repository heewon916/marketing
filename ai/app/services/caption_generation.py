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
from app.services.menu_promotion_context import StoreMenuCandidate
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

_DEFAULT_SYSTEM_INSTRUCTION = (
    "guide_text와 caption만 담은 JSON 객체 한 개만 한국어로 반환하세요."
)
_STRICT_KOREAN_SYSTEM_INSTRUCTION = (
    "guide_text와 caption만 담은 JSON 객체 한 개만 반환하세요. "
    "guide_text와 caption은 반드시 자연스러운 한국어로만 작성하고, "
    "영어 문장이나 영어 설명은 쓰지 마세요. "
    "브랜드명, 메뉴명, 고유명사, 해시태그처럼 꼭 필요한 짧은 표기만 예외로 허용합니다."
)
_STRICT_KOREAN_USER_SUFFIX = """

중요:
- guide_text와 caption은 반드시 한국어 문장으로 작성하세요.
- 영어 문장, 영어 설명, 영어 위주의 표현은 금지합니다.
- 브랜드명, 메뉴명, 고유명사처럼 꼭 필요한 짧은 영어만 제한적으로 허용합니다.
"""

_MENU_PROMOTION_PROMPT_TEMPLATE = """당신은 5060 소상공인의 메뉴 홍보를 위한 한국어 인스타그램 게시물 포스팅용 촬영 안내문과 캡션을 작성합니다.

규칙:
- 오직 JSON 객체 텍스트만 반환하세요.
- 다음 스키마를 사용하세요: {{"guide_text": "...", "caption": "..."}}.
- 게시물 목적은 "메뉴 홍보"입니다.
- "guide_text"는 사장님이 사진에서 어떤 점을 강조해야 하는지 알려주는 1문장의 한국어 문장이어야 합니다.
- "caption"은 레퍼런스 캡션과 유사한 구조로 구성된 감성적인 한국어 인스타그램 캡션이어야 합니다.
- 제공된 키워드를 자연스럽게 활용하세요. 관련 없는 상품을 임의로 만들어내지 마세요.
- 메뉴, 상품, 재료, 또는 매장에서 제공하는 것을 홍보하는 톤으로 작성하세요.
- 결과물은 동네 가게 사장님의 인스타그램 게시물에 어울리도록 작성하세요.
- "utterance"는 사장님이 직접 입력한 게시물의 핵심 메모입니다. caption은 반드시 이 메모의 의도와 주제를 중심으로 작성하고, keywords와 weather_context는 보조적으로 활용하세요. utterance가 "(없음)"이면 keywords와 weather_context만으로 작성하세요.
- "guide_text"는 utterance가 있으면 그 메모에 어울리는 장면을 어떻게 촬영할지 안내하세요.
- 모든 출력 값(guide_text, caption)은 반드시 한국어로 작성하세요.

레퍼런스 캡션들의 톤과 형식을 참고하되, 문장은 그대로 베끼지 말고 입력에 맞게 새로 작성하세요.

이제 아래 입력에 맞춰 동일한 형식의 JSON 객체 한 개만 출력하세요.

입력:
- owner_persona: {owner_persona}
- weather_context: {weather_context}
- utterance: {utterance}
- keywords: {keywords}

"""

_BUSINESS_NOTICE_PROMPT_TEMPLATE = """당신은 5060 소상공인의 영업변경 공지를 위한 한국어 인스타그램 게시물 포스팅용 촬영 안내문과 캡션을 작성합니다.

규칙:
- 오직 JSON 객체 텍스트만 반환하세요.
- 다음 스키마를 사용하세요: {{"guide_text": "...", "caption": "..."}}.
- 게시물 목적은 "영업 공지"입니다.
- "guide_text"는 사장님이 사진에서 어떤 점을 강조해야 하는지 알려주는 1문장의 한국어 문장이어야 합니다.
- "caption"은 레퍼런스 캡션과 유사한 구조로 구성된 감성적인 한국어 인스타그램 캡션이어야 합니다.
- 제공된 키워드를 자연스럽게 활용하세요. 관련 없는 상품을 임의로 만들어내지 마세요.
- 영업, 일정, 운영 가능 여부에 대한 명확한 영업 공지 톤으로 작성하세요.
- 결과물은 동네 가게 사장님의 인스타그램 게시물에 어울리도록 작성하세요.
- "utterance"는 사장님이 직접 입력한 게시물의 핵심 메모입니다. caption은 반드시 이 메모의 의도와 공지 내용을 중심으로 작성하고, keywords와 weather_context는 보조적으로 활용하세요. utterance가 "(없음)"이면 keywords와 weather_context만으로 작성하세요.
- "guide_text"는 utterance가 있으면 그 메모에 어울리는 장면을 어떻게 촬영할지 안내하세요.
- 모든 출력 값(guide_text, caption)은 반드시 한국어로 작성하세요.

레퍼런스 캡션들의 톤과 형식을 참고하되, 문장은 그대로 베끼지 말고 입력에 맞게 새로 작성하세요.

이제 아래 입력에 맞춰 동일한 형식의 JSON 객체 한 개만 출력하세요.

입력:
- owner_persona: {owner_persona}
- weather_context: {weather_context}
- utterance: {utterance}
- keywords: {keywords}
"""

_DAILY_SHARE_PROMPT_TEMPLATE = """당신은 5060 소상공인의 일상 공유를 위한 한국어 인스타그램 게시물 포스팅용 촬영 안내문과 캡션을 작성합니다.

규칙:
- 오직 JSON 객체 텍스트만 반환하세요.
- 다음 스키마를 사용하세요: {{"guide_text": "...", "caption": "..."}}.
- 게시물 목적은 "일상 공유"입니다.
- "guide_text"는 사장님이 사진에서 어떤 점을 강조해야 하는지 알려주는 1문장의 한국어 문장이어야 합니다.
- "caption"은 레퍼런스 캡션과 유사한 구조로 구성된 감성적인 한국어 인스타그램 캡션이어야 합니다.
- 제공된 키워드를 자연스럽게 활용하세요. 관련 없는 상품을 임의로 만들어내지 마세요.
- 사장님의 일상, 매장 분위기, 비하인드 순간을 공유하는 톤으로 작성하세요.
- 결과물은 동네 가게 사장님의 인스타그램 게시물에 어울리도록 작성하세요.
- "utterance"는 사장님이 직접 입력한 게시물의 핵심 메모입니다. caption은 반드시 이 메모의 의도와 주제를 중심으로 작성하고, keywords와 weather_context는 보조적으로 활용하세요. utterance가 "(없음)"이면 keywords와 weather_context만으로 작성하세요.
- "guide_text"는 utterance가 있으면 그 메모에 어울리는 장면을 어떻게 촬영할지 안내하세요.
- 모든 출력 값(guide_text, caption)은 반드시 한국어로 작성하세요.

레퍼런스 캡션들의 톤과 형식을 참고하되, 문장은 그대로 베끼지 말고 입력에 맞게 새로 작성하세요.

이제 아래 입력에 맞춰 동일한 형식의 JSON 객체 한 개만 출력하세요.

입력:
- owner_persona: {owner_persona}
- weather_context: {weather_context}
- utterance: {utterance}
- keywords: {keywords}
"""

DEFAULT_FALLBACK_GUIDE_TEXT = (
    "사장님, 가게 전경이 잘 나오도록 영상을 촬영해보세요."
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


class CaptionGenerationUnavailableError(RuntimeError):
    """Raised when caption generation is unavailable."""


class CaptionGenerationLanguageError(CaptionGenerationUnavailableError):
    """Raised when caption generation returns text that is not sufficiently Korean."""


@dataclass
class CaptionGenerationResult:
    guide_text: str
    draft_caption: str
    selected_menu_name: str | None = None

    @property
    def stored_caption(self) -> str:
        return self.draft_caption


@dataclass
class CaptionGenerationRequest:
    purpose: ContentPurpose
    keywords: list[str]
    owner_persona: str
    utterance: str = ""
    weather_tags: list[str] = field(default_factory=list)
    reference_captions: list[str] = field(default_factory=list)
    menu_candidates: list[StoreMenuCandidate] = field(default_factory=list)


@dataclass
class CaptionFallbackResult:
    result: CaptionGenerationResult
    fallback_source: str | None


class CaptionPipeline:
    def __init__(self, purpose: ContentPurpose, prompt_template: str) -> None:
        self.purpose = purpose
        self.prompt_template = prompt_template

    def build_prompt(self, request: CaptionGenerationRequest) -> str:
        prompt = self.prompt_template.format(
            owner_persona=request.owner_persona.strip(),
            weather_context=_build_weather_context(request.weather_tags),
            utterance=request.utterance.strip() or "(없음)",
            keywords=", ".join(request.keywords) if request.keywords else "(없음)",
        )
        if not request.reference_captions:
            return prompt
        reference_lines = "\n".join(
            f"{index}. {caption}"
            for index, caption in enumerate(request.reference_captions, start=1)
        )
        return (
            f"{prompt}\n\n"
            "참고용 레퍼런스 캡션:\n"
            f"{reference_lines}\n\n"
            "위 레퍼런스는 문체와 분위기를 참고하기 위한 예시입니다.\n"
            "문장을 그대로 복사하거나 해시태그를 재사용하지 말고, 현재 입력의 의도에 맞춰 새롭게 작성하세요."
        )

    def build_fallback(
        self,
        request: CaptionGenerationRequest,
        fallback_source: str | None,
    ) -> CaptionFallbackResult:
        draft_caption = self._build_fallback_caption(request)
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
            ),
            fallback_source=effective_fallback_source,
        )

    def _build_fallback_caption(self, request: CaptionGenerationRequest) -> str:
        keyword_phrase = (
            ", ".join(request.keywords) if request.keywords else "오늘의 매장"
        )
        weather_context = _build_weather_context(request.weather_tags)
        if weather_context != "특별한 날씨 포인트 없음":
            return (
                f"{weather_context} 분위기와 {request.owner_persona} 무드로 "
                f"{keyword_phrase}를 소개해보세요."
            )
        return f"{request.owner_persona} 무드로 {keyword_phrase}를 소개해보세요."

    def _build_fallback_guide_text(self, request: CaptionGenerationRequest) -> str:
        keyword_phrase = ", ".join(request.keywords)
        return (
            f"사장님, {keyword_phrase}이(가) 화면에서 잘 보이도록 구도와 초점을 먼저 맞춰보세요. "
            "촬영 전에는 주제가 또렷하게 드러나는지 한 번 더 확인해주세요."
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
        max_tokens: int = 256,
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
        self._response_format_supported: bool = True
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
            result = await self._generate_korean_result(prompt, purpose=request.purpose)
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
        *,
        strict_language: bool,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "messages": [
                {
                    "role": "system",
                    "content": self._build_system_instruction(
                        strict_language=strict_language
                    ),
                },
                {
                    "role": "user",
                    "content": self._build_user_prompt(
                        prompt,
                        strict_language=strict_language,
                    ),
                },
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
                    },
                    "required": ["guide_text", "caption"],
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
        strict_language: bool,
    ) -> httpx.Response:
        payload = self._build_request_payload(
            prompt,
            include_response_format,
            strict_language=strict_language,
        )
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
        if response.status_code != 400:
            return False
        body = response.text.lower()
        if "response_format" not in body:
            return False
        unsupported_markers = (
            "unsupported",
            "not supported",
            "unknown",
            "invalid",
        )
        return any(marker in body for marker in unsupported_markers)

    def _get_pipeline(self, purpose: ContentPurpose) -> CaptionPipeline:
        pipeline = self._pipelines.get(purpose)
        if pipeline is None:
            raise CaptionGenerationUnavailableError(
                f"Caption pipeline is not configured for purpose: {purpose}."
            )
        return pipeline

    async def _generate(
        self,
        prompt: str,
        *,
        purpose: ContentPurpose,
        strict_language: bool,
    ) -> str:
        if not self.base_url:
            raise CaptionGenerationUnavailableError(
                "Caption generation server base URL is not configured."
            )

        response: httpx.Response | None = None
        first_unsupported_status: int | None = None
        try:
            response = await self._post_chat_completion(
                prompt,
                include_response_format=self._response_format_supported,
                strict_language=strict_language,
            )
            if (
                self._response_format_supported
                and self._is_response_format_unsupported(response)
            ):
                first_unsupported_status = response.status_code
                self._response_format_supported = False
                logger.warning(
                    "Caption server reports response_format unsupported; "
                    "disabling for subsequent requests.",
                    extra=build_log_extra(
                        "caption_generation.response_format.disabled",
                        component="caption_generation",
                        stage="generate",
                        outcome="degraded",
                        purpose=purpose,
                        caption_http_status=first_unsupported_status,
                    ),
                )
                response = await self._post_chat_completion(
                    prompt,
                    include_response_format=False,
                    strict_language=strict_language,
                )
            response.raise_for_status()
        except httpx.TimeoutException as exc:
            raise TimeoutError from exc
        except httpx.HTTPStatusError as exc:
            detail = (
                f"Caption generation server returned HTTP {exc.response.status_code}."
            )
            if first_unsupported_status is not None:
                detail += (
                    f" Initial response_format request returned HTTP "
                    f"{first_unsupported_status}."
                )
            raise CaptionGenerationUnavailableError(detail) from exc
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
                caption_language_mode=(
                    "strict_korean_retry" if strict_language else "default"
                ),
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

    async def _generate_korean_result(
        self,
        prompt: str,
        *,
        purpose: ContentPurpose,
    ) -> CaptionGenerationResult:
        raw_output = await self._generate(
            prompt,
            purpose=purpose,
            strict_language=False,
        )
        try:
            return self._parse_generation_result(raw_output)
        except CaptionGenerationLanguageError:
            logger.warning(
                "Caption generation returned non-Korean text; retrying with stricter language guidance.",
                extra=build_log_extra(
                    "caption_generation.language_retry.attempted",
                    component="caption_generation",
                    stage="language_validation",
                    outcome="retrying",
                    purpose=purpose,
                    non_korean_detected=True,
                    language_retry_attempted=True,
                ),
            )

        raw_output = await self._generate(
            prompt,
            purpose=purpose,
            strict_language=True,
        )
        try:
            return self._parse_generation_result(raw_output)
        except CaptionGenerationLanguageError as exc:
            logger.warning(
                "Caption generation retry still returned non-Korean text.",
                extra=build_log_extra(
                    "caption_generation.language_retry.failed",
                    component="caption_generation",
                    stage="language_validation",
                    outcome="failed",
                    purpose=purpose,
                    non_korean_detected=True,
                    language_retry_attempted=True,
                    language_retry_failed=True,
                ),
            )
            raise exc

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

        if not guide_text or not draft_caption:
            raise CaptionGenerationUnavailableError(
                "Caption generation returned incomplete text fields."
            )

        self._validate_korean_output(guide_text, draft_caption)

        return CaptionGenerationResult(
            guide_text=guide_text,
            draft_caption=draft_caption,
        )

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()

    @staticmethod
    def _build_system_instruction(*, strict_language: bool) -> str:
        if strict_language:
            return _STRICT_KOREAN_SYSTEM_INSTRUCTION
        return _DEFAULT_SYSTEM_INSTRUCTION

    @staticmethod
    def _build_user_prompt(prompt: str, *, strict_language: bool) -> str:
        if strict_language:
            return f"{prompt}{_STRICT_KOREAN_USER_SUFFIX}"
        return prompt

    def _validate_korean_output(self, guide_text: str, draft_caption: str) -> None:
        if self._looks_non_korean(guide_text) or self._looks_non_korean(draft_caption):
            raise CaptionGenerationLanguageError(
                "Caption generation returned text that is not sufficiently Korean."
            )

    @staticmethod
    def _looks_non_korean(text: str) -> bool:
        hangul_count = len(re.findall(r"[가-힣]", text))
        ascii_count = len(re.findall(r"[A-Za-z]", text))
        if hangul_count == 0:
            return True
        if ascii_count == 0:
            return False
        return ascii_count > hangul_count * 1.5


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
