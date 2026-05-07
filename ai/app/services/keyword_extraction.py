from __future__ import annotations
from dataclasses import dataclass, field
import json
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import Request
import httpx

from app.core.config import (
    DEFAULT_KEYWORD_MODEL_PATH,
    settings,
)
from app.logging import build_log_extra, preview_text
# Legacy local GGUF bootstrap is intentionally disabled during llama-server migration.
# from app.keyword_model_download import ensure_keyword_model_available

logger = logging.getLogger(__name__)
# TOODO : 조사, 어미, 접미사 등 키워드 코드 외부로 빼고 모듈로 만들기 -> 모듈 가져와서 사용하는 방식으로 리팩토링하기 
_GENERIC_KEYWORDS = {
    "오늘",
    "요즘",
    "그래도",
    "손님",
    "매장",
    "가게",
    "분위기",
    "기분",
    "하늘",
    "날씨",
    "상황",
    "진열장",
    "먹고 살기",
    "만만치 않다",
    "만만치",
    "제철",
}

_WEATHER_SIGNAL_HINTS = (
    "맑",
    "비",
    "눈",
    "흐",
    "바람",
    "쌀쌀",
    "선선",
    "후텁",
    "무더",
    "포근",
    "서늘",
    "따뜻",
    "추위",
    "더위",
    "장마",
    "봄",
    "여름",
    "가을",
    "겨울",
    "초여름",
    "초가을",
)

_PURE_WEATHER_SIGNALS = {
    "맑음",
    "비",
    "눈",
    "흐림",
    "흐린 날",
    "맑은 날",
    "비 오는 날",
    "눈 오는 날",
    "바람",
    "봄바람",
    "쌀쌀함",
    "선선함",
    "후텁지근함",
    "무더위",
    "포근함",
    "서늘함",
    "따뜻함",
    "추위",
    "더위",
    "장마",
    "봄",
    "여름",
    "가을",
    "겨울",
    "초여름",
    "초가을",
}

_MORPH_ALLOWED_KEYWORD_TAG_PREFIXES = ("N", "SL", "SH", "SN", "XR")
_MORPH_ALLOWED_WEATHER_TAG_PREFIXES = ("N", "SL", "SH", "SN", "XR", "V")
_MORPH_DISALLOWED_TAIL_TAGS = {
    "JKS",
    "JKC",
    "JKG",
    "JKO",
    "JKB",
    "JKV",
    "JKQ",
    "JX",
    "JC",
    "EP",
    "EF",
    "EC",
    "ETN",
    "ETM",
    "SF",
    "SP",
    "SS",
    "SE",
    "SO",
    "SW",
}
_WEATHER_CANONICAL_BY_HINT = (
    ("봄바람", "봄바람"),
    ("초여름", "초여름"),
    ("초가을", "초가을"),
    ("장마", "장마"),
    ("쌀쌀", "쌀쌀함"),
    ("선선", "선선함"),
    ("후텁", "후텁지근함"),
    ("무더", "무더위"),
    ("포근", "포근함"),
    ("서늘", "서늘함"),
    ("따뜻", "따뜻함"),
    ("추위", "추위"),
    ("더위", "더위"),
    ("맑", "맑음"),
    ("흐", "흐림"),
    ("비", "비"),
    ("눈", "눈"),
    ("봄", "봄"),
    ("여름", "여름"),
    ("가을", "가을"),
    ("겨울", "겨울"),
)

_PROMPT_TEMPLATE = """You extract Instagram-worthy Korean promotional angles from a raw shop-owner utterance.

Rules:
- Return JSON object text only.
- Use this schema: {{"draft_keywords": ["..."], "weather_signals": ["..."]}}.
- "draft_keywords" must contain 1 to 3 short Korean noun phrases that are good Instagram content 소재.
- "weather_signals" must contain 0 to 3 short Korean weather or season signals found in the utterance.
- Keep "draft_keywords" focused on menu, drink, dessert, ingredient, product, prop, or seasonal promotional phrases such as "제철 음식".
- Drop filler talk, complaints, mood-only phrases, and general situation words.
- Preserve useful noun phrases and deduplicate everything.
- If menu/ingredient and promotional concept both matter, keep both in "draft_keywords".
- Do not put weather words inside "draft_keywords". Put them in "weather_signals" instead.

Examples:
Input: \uc624\ub298 \uc544\uc8fc \ube44\uc2fc \ubc14\ub2d0\ub77c\ub85c \ubc84\ud130 \ucfe0\ud0a4\ub97c \uad6c\uc6e0\ub294\ub370 \uc190\ub2d8\uc774 \uc601 \uc5c6\ub124...
Output: {{"draft_keywords": ["\ubc84\ud130 \ucfe0\ud0a4"], "weather_signals": []}}

Input: \uc624\ub298 \ube44\ub3c4 \uc624\uace0 \uc601 \ud558\ub298\uc774 \uafb8\ubb3c\uac70\ub9ac\ub294\ub370 \ub9c9\uac78\ub9ac\ub791 \ud30c\uc804\uc774 \ub531\uc774\uaca0\ub2e4
Output: {{"draft_keywords": ["\ub9c9\uac78\ub9ac", "\ud30c\uc804"], "weather_signals": ["\ube44"]}}

Input: \uc624\ub298 \ub538\ub798\ubbf8\uac00 \uc601\uad6d \ube48\ud2f0\uc9c0\uc0f5\uc5d0\uc11c \uace0\uae09 \ucc3b\uc794\uc744 \uac00\uc838\uc640\uc11c \uc9c4\uc5f4\uc7a5\uc5d0 \uc0c8\ub85c \ub460\uc5b4.
Output: {{"draft_keywords": ["\ucc3b\uc794"], "weather_signals": []}}

Input: \uc694\uc998 \uba39\uace0 \uc0b4\uae30 \ub9cc\ub9cc\uce58 \uc54a\ub2e4.. \uadf8\ub798\ub3c4 \uc81c\ucca0 \uc74c\uc2dd\uc740 \uba39\uace0 \uc0b4\uc544\uc57c\uc9c0.. \ubc24\ud638\ubc15\uc774 \uc694.uc774
Output: {{"draft_keywords": ["\ubc24\ud638\ubc15", "\uc81c\ucca0 \uc74c\uc2dd"], "weather_signals": []}}

Input: \ubd04\ubc14\ub78c \uc0b4\ub791\ubd80\ub294 \ub0a0\uc5d0\ub294 \ub538\uae30 \ub77c\ub5bc\ub791 \ubd04 \ub514\uc800\ud2b8 \uc62c\ub9ac\uace0 \uc2f6\ub2e4
Output: {{"draft_keywords": ["\ub538\uae30 \ub77c\ub5bc", "\ubd04 \ub514\uc800\ud2b8"], "weather_signals": ["\ubd04\ubc14\ub78c"]}}

Input: {utterance}
Output:
"""

_ALLOWED_PURPOSES = (
    "메뉴 홍보",
    "영업 공지",
    "일상 공유",
)

_PROMPT_TEMPLATE = """You classify the purpose of a Korean shop-owner utterance and extract 1 to 3 reusable keyword candidates.

Rules:
- Return JSON object text only.
- Use this schema: {{"purpose": "...", "keywords": ["..."]}}.
- "purpose" must be exactly one of: "메뉴 홍보", "영업 공지", "일상 공유".
- "keywords" must contain 1 to 3 short Korean keyword candidates copied or lightly normalized from the utterance.
- Keep "keywords" focused on menu, product, event, notice, routine, or shop-operation phrases.
- Drop filler talk, complaints, mood-only phrases, and general situation words.
- Preserve useful phrases and deduplicate everything.
- Do not explain your reasoning.

Examples:
Input: \uc624\ub298 \uc544\uc8fc \ube44\uc2fc \ubc14\ub2d0\ub77c\ub85c \ubc84\ud130 \ucfe0\ud0a4\ub97c \uad6c\uc6e0\ub294\ub370 \uc190\ub2d8\uc774 \uc601 \uc5c6\ub124...
Output: {{"purpose": "메뉴 홍보", "keywords": ["\ubc84\ud130 \ucfe0\ud0a4"]}}

Input: \uc624\ub298 \ube44\ub3c4 \uc624\uace0 \uc601 \ud558\ub298\uc774 \uafb8\ubb3c\uac70\ub9ac\ub294\ub370 \ub9c9\uac78\ub9ac\ub791 \ud30c\uc804\uc774 \ub531\uc774\uaca0\ub2e4
Output: {{"purpose": "메뉴 홍보", "keywords": ["\ub9c9\uac78\ub9ac", "\ud30c\uc804"]}}

Input: \uc624\ub298 \uc784\uc2dc\ud734\ubb34\ub77c\uc11c \uc800\ub141 \uc601\uc5c5\uc740 \uc26c\uace0 \ub0b4\uc77c \uc815\uc0c1\uc601\uc5c5\ud560\uac8c\uc694
Output: {{"purpose": "영업 공지", "keywords": ["\uc784\uc2dc \ud734\ubb34", "\uc815\uc0c1\uc601\uc5c5"]}}

Input: \uc624\ub298\uc740 \uac00\uac8c \ub9c8\uac10\ud558\uace0 \uc9d1\uc5d0\uc11c \ucc45 \uc77d\uc73c\uba74\uc11c \uc27d\ub2c8\ub2e4
Output: {{"purpose": "일상 공유", "keywords": ["\uac00\uac8c \ub9c8\uac10", "\ucc45 \uc77d\uae30"]}}

Input: {utterance}
Output:
"""


class KeywordExtractionUnavailableError(RuntimeError):
    """Raised when the local keyword extraction model is unavailable."""


@dataclass
class KeywordExtractionResult:
    draft_keywords: list[str]
    weather_signals: list[str]
    final_keywords: list[str] = field(default_factory=list)


class KeywordExtractionService:
    def __init__(
        self,
        model_path: Path,
        enabled: bool = True,
        n_ctx: int = 2048,
        max_tokens: int = 64,
        temperature: float = 0.1,
        top_p: float = 0.9,
        n_threads: int = 1,
        n_gpu_layers: int = 20,
        timeout_seconds: float = 10.0,
        base_url: str | None = None,
        chat_endpoint: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.model_path = model_path
        self.enabled = enabled
        self.n_ctx = n_ctx
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.n_threads = n_threads
        self.n_gpu_layers = n_gpu_layers
        self.timeout_seconds = timeout_seconds
        self.base_url = (base_url or "").rstrip("/")
        self.chat_endpoint = chat_endpoint or "/v1/chat/completions"
        self.api_key = api_key
        self._server_checked = False
        self._morph_analyzer: Any = None
        self._morph_analyzer_initialized = False
        self._lock = threading.Lock()

    async def preload(self) -> None:
        await self._check_server_connection()

    async def extract_keywords(self, utterance: str) -> KeywordExtractionResult:
        if not self.enabled:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction model is disabled."
            )

        prompt = _PROMPT_TEMPLATE.format(utterance=utterance.strip())
        started_at = time.perf_counter()

        logger.info(
            "Keyword extraction inference started.",
            extra=build_log_extra(
                "keyword_extraction.inference.started",
                component="keyword_extraction",
                stage="inference",
                outcome="started",
                keyword_timeout_seconds=self.timeout_seconds,
                keyword_model_base_url=self.base_url,
                keyword_chat_endpoint=self.chat_endpoint,
                keyword_server_checked=self._server_checked,
                utterance_length=len(utterance),
                utterance_preview=preview_text(
                    utterance,
                    settings.LOG_EVENT_PREVIEW_MAX_LEN,
                )
                if settings.LOG_INCLUDE_RAW_IDENTIFIERS
                else None,
            ),
        )

        try:
            raw_output = await self._generate_keywords(prompt)
        except TimeoutError as exc:
            logger.warning(
                "Keyword extraction timed out while waiting for llama-server completion.",
                extra=build_log_extra(
                    "keyword_extraction.inference.completed",
                    component="keyword_extraction",
                    stage="inference",
                    outcome="failed",
                    error_type="TimeoutError",
                    keyword_timeout_seconds=self.timeout_seconds,
                    elapsed_ms=int((time.perf_counter() - started_at) * 1000),
                    keyword_model_base_url=self.base_url,
                    keyword_chat_endpoint=self.chat_endpoint,
                ),
            )
            raise KeywordExtractionUnavailableError(
                "Keyword extraction timed out."
            ) from exc
        except KeywordExtractionUnavailableError:
            raise
        except Exception as exc:
            logger.warning(
                "Keyword extraction inference raised an unexpected exception.",
                extra=build_log_extra(
                    "keyword_extraction.inference.completed",
                    component="keyword_extraction",
                    stage="inference",
                    outcome="failed",
                    error_type=exc.__class__.__name__,
                    elapsed_ms=int((time.perf_counter() - started_at) * 1000),
                    keyword_model_base_url=self.base_url,
                    keyword_chat_endpoint=self.chat_endpoint,
                ),
                exc_info=True,
            )
            raise KeywordExtractionUnavailableError(
                "Keyword extraction inference failed."
            ) from exc

        result = self._parse_extraction_result(raw_output)
        logger.info(
            "Keyword extraction inference finished.",
            extra=build_log_extra(
                "keyword_extraction.inference.completed",
                component="keyword_extraction",
                stage="inference",
                outcome="succeeded",
                elapsed_ms=int((time.perf_counter() - started_at) * 1000),
                draft_keyword_count=len(result.draft_keywords),
                draft_keywords_preview=", ".join(result.draft_keywords),
                weather_signal_count=len(result.weather_signals),
                weather_signals_preview=", ".join(result.weather_signals),
            ),
        )
        return result

    def _build_request_payload(self, prompt: str, include_response_format: bool) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only a JSON object with purpose and keywords fields."
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
                        "purpose": {
                            "type": "string",
                            "enum": list(_ALLOWED_PURPOSES),
                        },
                        "keywords": {
                            "type": "array",
                            "minItems": 1,
                            "maxItems": 3,
                            "items": {"type": "string"},
                        },
                    },
                    "required": ["purpose", "keywords"],
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
            raise KeywordExtractionUnavailableError(
                "Keyword extraction server base URL is not configured."
            )

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(self._chat_url)
        except httpx.TimeoutException as exc:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction server connectivity check timed out."
            ) from exc
        except httpx.HTTPError as exc:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction server connectivity check failed."
            ) from exc

        self._server_checked = True
        logger.info(
            "Keyword extraction server connectivity check completed.",
            extra=build_log_extra(
                "keyword_extraction.server_check.completed",
                component="keyword_extraction",
                stage="server_check",
                outcome="succeeded",
                keyword_model_base_url=self.base_url,
                keyword_chat_endpoint=self.chat_endpoint,
                keyword_http_status=response.status_code,
            ),
        )

    @staticmethod
    def _is_response_format_unsupported(response: httpx.Response) -> bool:
        if response.status_code < 400:
            return False
        body = response.text.lower()
        return "response_format" in body or "json_object" in body or "schema" in body

    async def _generate_keywords(self, prompt: str) -> str:
        if not self.base_url:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction server base URL is not configured."
            )

        generation_started_at = time.perf_counter()
        logger.info(
            "Calling llama-server chat completion for keyword extraction.",
            extra=build_log_extra(
                "keyword_extraction.generate.started",
                component="keyword_extraction",
                stage="generate",
                outcome="started",
                keyword_max_tokens=self.max_tokens,
                keyword_temperature=self.temperature,
                keyword_top_p=self.top_p,
            ),
        )

        response: httpx.Response | None = None
        try:
            response = await self._post_chat_completion(
                prompt,
                include_response_format=True,
            )
            if self._is_response_format_unsupported(response):
                logger.info(
                    "llama-server response_format is unsupported; retrying without schema enforcement.",
                    extra=build_log_extra(
                        "keyword_extraction.generate.response_format_retry",
                        component="keyword_extraction",
                        stage="generate",
                        outcome="retrying",
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
            raise KeywordExtractionUnavailableError(
                f"Keyword extraction server returned HTTP {exc.response.status_code}."
            ) from exc
        except httpx.HTTPError as exc:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction server request failed."
            ) from exc

        self._server_checked = True
        response_payload = response.json()
        raw_output = (
            response_payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        logger.info(
            "llama-server keyword completion returned.",
            extra=build_log_extra(
                "keyword_extraction.generate.completed",
                component="keyword_extraction",
                stage="generate",
                outcome="succeeded",
                elapsed_ms=int((time.perf_counter() - generation_started_at) * 1000),
                keyword_model_base_url=self.base_url,
                keyword_chat_endpoint=self.chat_endpoint,
                keyword_http_status=response.status_code if response is not None else None,
                raw_output_preview=preview_text(
                    raw_output,
                    settings.LOG_EVENT_PREVIEW_MAX_LEN,
                ),
            ),
        )
        return raw_output

    # Legacy local llama-cpp flow is preserved as comments for rollback reference.
    # def _ensure_model(self):
    #     self.model_path = ensure_keyword_model_available(self.model_path)
    #     from llama_cpp import Llama
    #     self._model = Llama(
    #         model_path=str(self.model_path),
    #         n_ctx=self.n_ctx,
    #         n_threads=self.n_threads,
    #         n_gpu_layers=self.n_gpu_layers,
    #         verbose=False,
    #     )
    #     return self._model

    def _parse_extraction_result(self, raw_output: str) -> KeywordExtractionResult:
        parsed = self._load_extraction_payload(raw_output)
        draft_payload, weather_payload = self._split_extraction_payload(parsed)

        if not isinstance(draft_payload, list):
            raise KeywordExtractionUnavailableError(
                "Keyword extraction returned a non-list payload."
            )
        draft_keywords = self._normalize_keywords_payload(draft_payload)
        weather_signals = self._normalize_weather_payload(weather_payload)

        if not draft_keywords and not weather_signals:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction returned no usable draft_keywords or weather signals."
            )

        logger.info(
            "Keyword extraction parsed keywords.",
            extra=build_log_extra(
                "keyword_extraction.parse.completed",
                component="keyword_extraction",
                stage="parse",
                outcome="succeeded",
                draft_keywords_preview=", ".join(draft_keywords),
                weather_signals_preview=", ".join(weather_signals),
                raw_output_preview=preview_text(
                    raw_output,
                    settings.LOG_EVENT_PREVIEW_MAX_LEN,
                ),
            ),
        )
        return KeywordExtractionResult(
            draft_keywords=draft_keywords,
            weather_signals=weather_signals,
            final_keywords=list(draft_keywords),
        )

    def _parse_keywords(self, raw_output: str) -> list[str]:
        return self._parse_extraction_result(raw_output).draft_keywords

    @staticmethod
    def _extract_json_payload(raw_output: str) -> str:
        object_match = re.search(r"\{[\s\S]*\}", raw_output)
        if object_match is not None:
            return object_match.group(0)

        match = re.search(r"\[[\s\S]*\]", raw_output)
        if match is None:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction did not return JSON."
            )
        return match.group(0)

    def _load_extraction_payload(self, raw_output: str) -> Any:
        payload = self._extract_json_payload(raw_output)
        try:
            return json.loads(payload)
        except json.JSONDecodeError as exc:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction returned invalid JSON."
            ) from exc

    @staticmethod
    def _split_extraction_payload(
        payload: Any,
    ) -> tuple[Any, list[Any]]:
        if isinstance(payload, dict):
            weather_candidate = payload.get("weather_signals")
            weather_payload = weather_candidate if isinstance(weather_candidate, list) else []
            draft_payload = payload.get("draft_keywords")
            if draft_payload is None:
                draft_payload = payload.get("keywords")
            return draft_payload, weather_payload
        return payload, []

    def _normalize_keywords_payload(self, payload: list[Any]) -> list[str]:
        return self._normalize_unique_values(
            payload,
            normalizer=self._normalize_keyword,
        )

    def _normalize_weather_payload(self, payload: list[Any]) -> list[str]:
        return self._normalize_unique_values(
            payload,
            normalizer=self._normalize_weather_signal,
        )

    @staticmethod
    def _normalize_unique_values(
        payload: list[Any],
        normalizer,
        limit: int = 3,
    ) -> list[str]:
        normalized_values: list[str] = []
        seen_values: set[str] = set()

        for item in payload:
            if not isinstance(item, str):
                continue

            normalized = normalizer(item)
            if not normalized or normalized in seen_values:
                continue

            seen_values.add(normalized)
            normalized_values.append(normalized)
            if len(normalized_values) == limit:
                break

        return normalized_values

    def _get_morph_analyzer(self) -> Any | None:
        if self._morph_analyzer_initialized:
            return self._morph_analyzer

        with self._lock:
            if self._morph_analyzer_initialized:
                return self._morph_analyzer

            try:
                from kiwipiepy import Kiwi

                self._morph_analyzer = Kiwi()
                logger.info(
                    "Keyword morphology analyzer initialized.",
                    extra=build_log_extra(
                        "keyword_extraction.morph_analyzer_init.completed",
                        component="keyword_extraction",
                        stage="morph_analyzer_init",
                        outcome="succeeded",
                        morph_analyzer="kiwi",
                    ),
                )
            except Exception as exc:
                self._morph_analyzer = None
                logger.warning(
                    "Keyword morphology analyzer is unavailable; falling back to regex normalization.",
                    extra=build_log_extra(
                        "keyword_extraction.morph_analyzer_init.completed",
                        component="keyword_extraction",
                        stage="morph_analyzer_init",
                        outcome="failed",
                        error_type=exc.__class__.__name__,
                        morph_analyzer="kiwi",
                    ),
                    exc_info=True,
                )
            finally:
                self._morph_analyzer_initialized = True

        return self._morph_analyzer

    @staticmethod
    def _basic_normalize_text(text: str) -> str:
        normalized = text.strip().strip("\"'`")
        normalized = re.sub(r"^[\s\W_]+|[\s\W_]+$", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    @staticmethod
    def _fallback_strip_trailing_particles(text: str) -> str:
        stripped = re.sub(
            r"(이랑|랑|하고|에서|으로|로|은|는|이|가|을|를|와|과|도|만|엔|에|의)$",
            "",
            text,
        )
        return stripped.strip()

    def _normalize_keyword(self, keyword: str) -> str:
        normalized = self._basic_normalize_text(keyword)
        if not normalized:
            return ""

        morphology_normalized = self._normalize_phrase_with_morphology(
            normalized,
            target="keyword",
        )
        if morphology_normalized is None:
            return self._fallback_normalize_keyword(normalized)
        if morphology_normalized:
            return morphology_normalized
        return ""

    def _normalize_weather_signal(self, signal: str) -> str:
        normalized = self._basic_normalize_text(signal)
        if not normalized:
            return ""

        morphology_normalized = self._normalize_phrase_with_morphology(
            normalized,
            target="weather_signal",
        )
        if morphology_normalized is None:
            return self._fallback_normalize_weather_signal(normalized)
        if morphology_normalized:
            return morphology_normalized
        return ""

    def _normalize_phrase_with_morphology(
        self,
        text: str,
        target: str,
    ) -> str | None:
        analyzer = self._get_morph_analyzer()
        if analyzer is None:
            return None

        try:
            tokens = analyzer.tokenize(text)
        except Exception as exc:
            logger.warning(
                "Keyword morphology analysis failed; falling back to regex normalization.",
                extra=build_log_extra(
                    "keyword_extraction.morph_analysis.completed",
                    component="keyword_extraction",
                    stage="morph_analysis",
                    outcome="failed",
                    error_type=exc.__class__.__name__,
                    morph_target=target,
                ),
                exc_info=True,
            )
            return None

        if target == "keyword":
            return self._normalize_keyword_tokens(tokens)
        return self._normalize_weather_tokens(tokens, text)

    def _normalize_keyword_tokens(self, tokens: list[Any]) -> str:
        pieces: list[str] = []

        for token in tokens:
            form = getattr(token, "form", "").strip()
            tag = getattr(token, "tag", "")
            if not form or not tag:
                continue
            if tag in _MORPH_DISALLOWED_TAIL_TAGS or tag in {"MAG", "MAJ", "IC"}:
                continue
            if tag.startswith("V") or tag in {"XSV", "XSA", "VCP", "VCN"}:
                if pieces:
                    break
                continue
            if tag.startswith(_MORPH_ALLOWED_KEYWORD_TAG_PREFIXES):
                pieces.append(form)
                continue
            if pieces:
                break

        normalized = " ".join(pieces)
        return self._fallback_normalize_keyword(normalized)

    def _normalize_weather_tokens(self, tokens: list[Any], original_text: str) -> str:
        pieces: list[str] = []

        for token in tokens:
            form = getattr(token, "form", "").strip()
            tag = getattr(token, "tag", "")
            if not form or not tag:
                continue
            if tag in _MORPH_DISALLOWED_TAIL_TAGS or tag in {"MAG", "MAJ", "IC"}:
                continue
            if tag.startswith(_MORPH_ALLOWED_WEATHER_TAG_PREFIXES):
                pieces.append(form)

        canonical = self._canonicalize_weather_signal(" ".join(pieces))
        if canonical:
            return canonical
        return self._fallback_normalize_weather_signal(original_text)

    def _fallback_normalize_keyword(self, keyword: str) -> str:
        normalized = self._basic_normalize_text(keyword)
        normalized = self._fallback_strip_trailing_particles(normalized)

        if len(normalized) < 2:
            return ""
        if len(normalized) > 20:
            return ""
        if normalized in _PURE_WEATHER_SIGNALS:
            return ""
        if normalized in _GENERIC_KEYWORDS:
            return ""
        if re.search(r"(다|요|네|죠|군)$", normalized):
            return ""
        if not re.search(r"[가-힣A-Za-z0-9]", normalized):
            return ""
        return normalized

    def _fallback_normalize_weather_signal(self, signal: str) -> str:
        normalized = self._basic_normalize_text(signal)
        normalized = self._fallback_strip_trailing_particles(normalized)
        return self._canonicalize_weather_signal(normalized)

    @staticmethod
    def _canonicalize_weather_signal(signal: str) -> str:
        normalized = KeywordExtractionService._basic_normalize_text(signal)
        if len(normalized) < 1:
            return ""
        if len(normalized) > 20:
            return ""
        if not re.search(r"[가-힣A-Za-z]", normalized):
            return ""

        for hint, canonical in _WEATHER_CANONICAL_BY_HINT:
            if hint in normalized:
                return canonical

        if not any(hint in normalized for hint in _WEATHER_SIGNAL_HINTS):
            return ""
        return normalized


def build_keyword_extraction_service() -> KeywordExtractionService:
    return KeywordExtractionService(
        model_path=DEFAULT_KEYWORD_MODEL_PATH,
        enabled=settings.KEYWORD_MODEL_ENABLED,
        n_ctx=settings.KEYWORD_MODEL_CTX_SIZE,
        max_tokens=settings.KEYWORD_MODEL_MAX_TOKENS,
        temperature=settings.KEYWORD_MODEL_TEMPERATURE,
        top_p=settings.KEYWORD_MODEL_TOP_P,
        n_threads=settings.KEYWORD_MODEL_THREADS,
        n_gpu_layers=settings.KEYWORD_MODEL_GPU_LAYERS,
        timeout_seconds=settings.KEYWORD_MODEL_TIMEOUT_SECONDS,
        base_url=settings.KEYWORD_MODEL_BASE_URL,
        chat_endpoint=settings.KEYWORD_MODEL_CHAT_ENDPOINT,
        api_key=settings.KEYWORD_MODEL_API_KEY,
    )


def get_keyword_extraction_service(request: Request) -> KeywordExtractionService:
    service = getattr(request.app.state, "keyword_extraction_service", None)
    if service is None:
        raise RuntimeError("Keyword extraction service is not initialized.")
    return service
