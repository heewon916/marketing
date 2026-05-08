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

_MENU_PROMOTION_PROMPT_TEMPLATE = """당신은 소상공인을 위한 짧은 한국어 인스타그램 마케팅 문구를 작성합니다.

규칙:
- 오직 JSON 객체 텍스트만 반환하세요.
- 다음 스키마를 사용하세요: {{"guide_text": "...", "caption": "..."}}.
- 게시물 목적은 "메뉴 홍보"입니다.
- "guide_text"는 사장님이 사진에서 어떤 점을 강조해야 하는지 알려주는 1~2문장의 한국어 문장이어야 합니다.
- "caption"은 1~3개의 짧은 문장으로 구성된 따뜻한 한국어 인스타그램 캡션이어야 합니다.
- 제공된 키워드를 자연스럽게 활용하세요. 관련 없는 상품을 임의로 만들어내지 마세요.
- 메뉴, 상품, 재료, 또는 매장에서 제공하는 것을 홍보하는 톤으로 작성하세요.
- 결과물은 동네 가게 사장님의 인스타그램 게시물에 어울리도록 작성하세요.
- 모든 출력 값(guide_text, caption)은 반드시 한국어로 작성하세요.

아래 예시들의 톤과 형식을 참고하되, 문장은 그대로 베끼지 말고 입력에 맞게 새로 작성하세요.

예시 1:
입력:
- owner_persona: "aesthetic" 
- weather_context: "TEMP_HOT
- keywords: "무화과", "여름"
출력:
{{"guide_text":"사장님, 손님들에게 한여름의 무화과를 영상에 담아 보여주세요.",
"caption": "늦여름의 맛 무화과 fig!

집에서도 밖에서도 먹은 무화과. 오묘한 생김새와 달큰한 맛이 매력적이다. 여름이 지나갈 때면 무화과를 꼭 챙겨 먹는다. 그냥 지나치면 아쉬운 마음. 속살은 분홍색과 상아색, 껍질은 연두색부터 짙은 자주색까지. 한입 앙 베어 물면 느껴지는 씨의 식감도 좋다!

#무화과 #fig #소월길밀영 #후암동 #후암동카페 #홈카페"}}

예시 2:
입력:
- owner_persona: "aesthetic"
- weather_context: "PRECIP_CLEAR"
- keywords: "봄", "레몬 타르트"
출력:
{{"guide_text":"사장님, 손님들에게 상큼한 레몬 타르트를 영상에 담아 보여주세요.",
"caption": "어디든 뭐든 좋은, 봄이로소이다 #lemontart"}}

이제 아래 입력에 맞춰 동일한 형식의 JSON 객체 한 개만 출력하세요.

입력:
- owner_persona: {owner_persona}
- weather_context: {weather_context}
- keywords: {keywords}
"""

_BUSINESS_NOTICE_PROMPT_TEMPLATE = """당신은 소상공인을 위한 짧은 한국어 인스타그램 마케팅 문구를 작성합니다.

규칙:
- 오직 JSON 객체 텍스트만 반환하세요.
- 다음 스키마를 사용하세요: {{"guide_text": "...", "caption": "...", "hashtags": ["#..."]}}.
- 게시물 목적은 "영업 공지"입니다.
- "guide_text"는 사장님이 사진에서 어떤 점을 강조해야 하는지 알려주는 1~2문장의 한국어 문장이어야 합니다.
- "caption"은 1~3개의 짧은 문장으로 구성된 따뜻한 한국어 인스타그램 캡션이어야 합니다.
- "hashtags"는 # 기호를 포함한 간결한 해시태그 1~5개를 담아야 합니다.
- 제공된 키워드를 자연스럽게 활용하세요. 관련 없는 상품을 임의로 만들어내지 마세요.
- 영업, 일정, 운영 가능 여부에 대한 명확한 영업 공지 톤으로 작성하세요.
- 결과물은 동네 가게 사장님의 인스타그램 게시물에 어울리도록 작성하세요.
- 모든 출력 값(guide_text, caption, hashtags)은 반드시 한국어로 작성하세요.

입력:
- owner_persona: {owner_persona}
- weather_context: {weather_context}
- keywords: {keywords}
"""

_DAILY_SHARE_PROMPT_TEMPLATE = """당신은 소상공인을 위한 짧은 한국어 인스타그램 마케팅 문구를 작성합니다.

규칙:
- 오직 JSON 객체 텍스트만 반환하세요.
- 다음 스키마를 사용하세요: {{"guide_text": "...", "caption": "...", "hashtags": ["#..."]}}.
- 게시물 목적은 "일상 공유"입니다.
- "guide_text"는 사장님이 사진에서 어떤 점을 강조해야 하는지 알려주는 1~2문장의 한국어 문장이어야 합니다.
- "caption"은 1~3개의 짧은 문장으로 구성된 따뜻한 한국어 인스타그램 캡션이어야 합니다.
- "hashtags"는 # 기호를 포함한 간결한 해시태그 1~5개를 담아야 합니다.
- 제공된 키워드를 자연스럽게 활용하세요. 관련 없는 상품을 임의로 만들어내지 마세요.
- 사장님의 일상, 매장 분위기, 비하인드 순간을 공유하는 톤으로 작성하세요.
- 결과물은 동네 가게 사장님의 인스타그램 게시물에 어울리도록 작성하세요.
- 모든 출력 값(guide_text, caption, hashtags)은 반드시 한국어로 작성하세요.

입력:
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
