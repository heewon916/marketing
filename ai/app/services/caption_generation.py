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

_MENU_PROMOTION_PROMPT_TEMPLATE = """당신은 5060 소상공인의 메뉴 홍보를 위한 한국어 인스타그램 게시물 포스팅용 촬영 안내문과 캡션을 작성합니다.

규칙:
- 오직 JSON 객체 텍스트만 반환하세요.
- 다음 스키마를 사용하세요: {{"guide_text": "...", "caption": "..."}}.
- 게시물 목적은 "메뉴 홍보"입니다.
- "guide_text"는 사장님이 사진에서 어떤 점을 강조해야 하는지 알려주는 1~2문장의 한국어 문장이어야 합니다.
- "caption"은 1~3개의 짧은 문장으로 구성된 따뜻한 한국어 인스타그램 캡션이어야 합니다.
- 제공된 키워드를 자연스럽게 활용하세요. 관련 없는 상품을 임의로 만들어내지 마세요.
- 메뉴, 상품, 재료, 또는 매장에서 제공하는 것을 홍보하는 톤으로 작성하세요.
- 결과물은 동네 가게 사장님의 인스타그램 게시물에 어울리도록 작성하세요.
- "utterance"는 사장님이 직접 입력한 게시물의 핵심 메모입니다. caption은 반드시 이 메모의 의도와 주제를 중심으로 작성하고, keywords와 weather_context는 보조적으로 활용하세요. utterance가 "(없음)"이면 keywords와 weather_context만으로 작성하세요.
- "guide_text"는 utterance가 있으면 그 메모에 어울리는 장면을 어떻게 촬영할지 안내하세요.
- 모든 출력 값(guide_text, caption)은 반드시 한국어로 작성하세요.

아래 예시들의 톤과 형식을 참고하되, 문장은 그대로 베끼지 말고 입력에 맞게 새로 작성하세요.

예시 1:
입력:
- owner_persona: "aesthetic"
- weather_context: "TEMP_HOT
- utterance: "어제 그 무화과가 처음 들어와서 자랑하고 싶어"
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
- utterance: "봄이라 좀 상콤한 거 잘 나갈까 싶어러 레몬 타르트 만들었아ㅓ"
- keywords: "봄", "레몬 타르트"
출력:
{{"guide_text":"사장님, 손님들에게 상큼한 레몬 타르트를 영상에 담아 보여주세요.",
"caption": "어디든 뭐든 좋은, 봄이로소이다 #lemontart"}}

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
- "guide_text"는 사장님이 사진에서 어떤 점을 강조해야 하는지 알려주는 1~2문장의 한국어 문장이어야 합니다.
- "caption"은 1~3개의 짧은 문장으로 구성된 따뜻한 한국어 인스타그램 캡션이어야 합니다.
- 제공된 키워드를 자연스럽게 활용하세요. 관련 없는 상품을 임의로 만들어내지 마세요.
- 영업, 일정, 운영 가능 여부에 대한 명확한 영업 공지 톤으로 작성하세요.
- 결과물은 동네 가게 사장님의 인스타그램 게시물에 어울리도록 작성하세요.
- "utterance"는 사장님이 직접 입력한 게시물의 핵심 메모입니다. caption은 반드시 이 메모의 의도와 공지 내용을 중심으로 작성하고, keywords와 weather_context는 보조적으로 활용하세요. utterance가 "(없음)"이면 keywords와 weather_context만으로 작성하세요.
- "guide_text"는 utterance가 있으면 그 메모에 어울리는 장면을 어떻게 촬영할지 안내하세요.
- 모든 출력 값(guide_text, caption)은 반드시 한국어로 작성하세요.

아래 예시들의 톤과 형식을 참고하되, 문장은 그대로 베끼지 말고 입력에 맞게 새로 작성하세요.

예시 1:
입력:
- owner_persona: "aesthetic"
- weather_context: "TEMP_FREEZING"
- utterance: "이번주 화수 이틀 쉬어"
- keywords: "케이크", "가족"
출력:
{{"guide_text":"사장님, 손님들에게 공방의 케익 작업을 영상에 담아 보여주세요.",
"caption": "아드님이 원하는 학교에 합격해서인가? 홀가분하고 개운한 얼굴로 등장한 또래의 지인 손님 한 분, 학생 때부터 봐오고 있는 모 양은 직장생활의 분투 속에서 내년엔 독립을 예정하고 있다니 그 새로운 장(章)에 나도 설레네. 어떻게 지내시나 궁금했던 한 분은 마음이 통했나? 마침 크리스마스 카드같은 긴 문자를 보내어 다시 새로운 남자친구와 교제중이라니 더 좋은 사람 나올 때까지 계속 만나자! 다행인 일일세.13월이란 없으니 그래서 12월의 안부는 각별한.

지난 며칠 밤샘에 가까운 부인의 케익 작업을 옆에서 거들면서 내년엔 공방일에 더 힘을 보태야겠다는 의무와 같은 생각이 드는게.. 계속해서 발전하는 생활은 못되더라도 갱신하려는 생활, 적어도 시간에 그저 흘러가지 않게끔 영점조정은 매번 필요한 것같다.

크리스마스 케익 분출까지 무탈히 마치고, 최고의 케익은 아니지만 올해도 밀영이 할 수 있는 최선에 가까운 충실함은 다하려 했으니 알아주시는 분들 있다면 깊은 감사를.

제품들도 떨어지고 밀영도 쉴 겸 이번주는 내일(화)과 모레(수) 이틀 쉬고 마지막 남은 며칠 잘 마무리해보겠습니다"}}

예시 2:
입력:
- owner_persona: "aesthetic"
- weather_context: "TEMP_MILD"
- utterance: "짧은 휴식 다녀와 오늘부터 다시 문 열어"
- keywords: "휴식", "시간"
출력:
{{"guide_text":"사장님, 사장님의 휴식 시간을 영상에 담아 보여주세요.",
"caption": "오래됐어도 낡지만은 않고, 호수처럼 잔잔하고 순한 시간이 흐르는 곳.. 딱히 내세울 건 없지만 그 자리에서 서로에게 어울리고 전체로서 보기 좋은 동네들 - 일테면 몇 해전까지 후암동, 하동, 울릉도, 타이베이 그리고 이번에 처음 찾은 보령도 그런 느낌.

가게를 하면 의지와 상관없이 긴 시간 지켜보게 되는 손님들이 생기는데 한 분 두 분 자기 업을 차근차근 준비하고 너무나도 훌륭하게 시작하는 모습을 보면 그 시절 나는 그랬던가 늦게나마 분발심이 발동하면서도 무엇보다 기쁩니다. @la_fassona

어제까지 이틀밤 짧은 휴식이었지만 만난 분들 지낸 님들 덕분인지 오랜 시간 자리를 비우고 온 기분. 화요일 되돌아가신 분들께는 송구하옵고, 오늘부터 다시 문 열고 있습니다."}}

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
- "guide_text"는 사장님이 사진에서 어떤 점을 강조해야 하는지 알려주는 1~2문장의 한국어 문장이어야 합니다.
- "caption"은 1~3개의 짧은 문장으로 구성된 따뜻한 한국어 인스타그램 캡션이어야 합니다.
- 제공된 키워드를 자연스럽게 활용하세요. 관련 없는 상품을 임의로 만들어내지 마세요.
- 사장님의 일상, 매장 분위기, 비하인드 순간을 공유하는 톤으로 작성하세요.
- 결과물은 동네 가게 사장님의 인스타그램 게시물에 어울리도록 작성하세요.
- "utterance"는 사장님이 직접 입력한 게시물의 핵심 메모입니다. caption은 반드시 이 메모의 의도와 주제를 중심으로 작성하고, keywords와 weather_context는 보조적으로 활용하세요. utterance가 "(없음)"이면 keywords와 weather_context만으로 작성하세요.
- "guide_text"는 utterance가 있으면 그 메모에 어울리는 장면을 어떻게 촬영할지 안내하세요.
- 모든 출력 값(guide_text, caption)은 반드시 한국어로 작성하세요.

아래 예시들의 톤과 형식을 참고하되, 문장은 그대로 베끼지 말고 입력에 맞게 새로 작성하세요.

예시 1:
입력:
- owner_persona: "aesthetic"
- weather_context: "SPECIAL_SEASONAL_CHANGE"
- utterance: "환절기에 좀 힘들었더니 옛날에 회사 다닐 때 생각이 많이 나더라"
- keywords: "일기", "시간"
출력:
{{"guide_text":"사장님, 사장님이 시간을 보내는 순간을 영상에 담아 보여주세요.",
"caption": "세상이 빙글빙글 몸은 기우뚱거리고. 나의 달팽이관이 자리를 잡지 못하고 방황했던 지난 며칠. 생경한 경험을 지나고 오늘에서야 기운을 내니 그새 이침 저녁 서늘한 바람이 부는 걸 이제서야 알아챈.

아파서 가게를 열지 못한 날이 없던 십년은 30대 회사원 시절에도 못그랬으니 참 신기한 일이면서도 "이젠 오늘이 가장 젊은 날" 엊그제 진찰을 하면서 던진 김 교수님 한 마디를 떠올려야 할 나이다.

이야기도 많고 참 길었던 이번 여름, 가게에서 익히 보았던 몇 분들에게선 새로운 면모이거나 조금은 더 살가워지거나.. 지난 일들도 가게 어딘가 차곡차곡 쌓여 있을 듯 싶다. 나도 모르게. 2023.9.1(금) 가을 첫날?"}}

예시 2:
입력:
- owner_persona: "aesthetic"
- weather_context: "PRECIP_HEAVY_RAIN"
- utterance: "가난한 사람들이라는 명작을 읽었는데 딸내미가 가엾더라. 손님들한테 내 감상을 공유하고 싶어"
- keywords: "독후감", "다정함"
출력:
{{"guide_text":"사장님, 사장님이 책을 읽은 공간과 책 표지를 영상에 담아 보여주세요.",
"caption": ""그의 어린 딸아이는 관에 기대어 있었는데 너무 가엾고 우울해 보였습니다. 깊은 생각에 잠겨 있늗 것 같았습니다! 바렌까, 저는 어린애가 생각에 잠기는 것이 정말 싫습니다. 기분이 안 좋아져요! ... "

가난이란 사람을 눅눅하게 만든다. 원래 그런 사람이 아닌 것을. 햇볕을 쬐면 잘 마른 빨래처럼 얼마든 다시 포송포송해질 수 있을텐데.

몇년째 집 서재방에서 햇볕에 타도록 묵혀둔 도스토옙스키의 #가난한사람들 , 미처 생각치 못한 결말의 프레드 울만 #동급생 . 가게 책모임에서 골라준 두 분과 여름 장마 덕에 그을린 시간에서 건져온."}}

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


@dataclass
class CaptionGenerationResult:
    guide_text: str
    draft_caption: str

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
            utterance=request.utterance.strip() or "(없음)",
            keywords=", ".join(request.keywords) if request.keywords else "none",
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
                        "guide_text와 caption만 담은 JSON 객체 한 개만 한국어로 반환하세요."
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

    async def _generate(self, prompt: str, *, purpose: ContentPurpose) -> str:
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

        if not guide_text or not draft_caption:
            raise CaptionGenerationUnavailableError(
                "Caption generation returned incomplete text fields."
            )

        return CaptionGenerationResult(
            guide_text=guide_text,
            draft_caption=draft_caption,
        )

    @staticmethod
    def _normalize_text(value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip()


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
