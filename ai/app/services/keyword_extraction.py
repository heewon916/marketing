from __future__ import annotations

import asyncio
from dataclasses import dataclass
import importlib.metadata
import json
import logging
import re
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import Request

from app.core.config import settings
from app.logging import build_log_extra, preview_text
from app.keyword_model_download import ensure_keyword_model_available

logger = logging.getLogger(__name__)

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

_PROMPT_TEMPLATE = """You extract Instagram-worthy Korean promotional angles from a raw shop-owner utterance.

Rules:
- Return JSON object text only.
- Use this schema: {{"keywords": ["..."], "weather_signals": ["..."]}}.
- "keywords" must contain 1 to 3 short Korean noun phrases that are good Instagram content 소재.
- "weather_signals" must contain 0 to 3 short Korean weather or season signals found in the utterance.
- Keep "keywords" focused on menu, drink, dessert, ingredient, product, prop, or seasonal promotional phrases such as "제철 음식".
- Drop filler talk, complaints, mood-only phrases, and general situation words.
- Preserve useful noun phrases and deduplicate everything.
- If menu/ingredient and promotional concept both matter, keep both in "keywords".
- Do not put weather words inside "keywords". Put them in "weather_signals" instead.

Examples:
Input: \uc624\ub298 \uc544\uc8fc \ube44\uc2fc \ubc14\ub2d0\ub77c\ub85c \ubc84\ud130 \ucfe0\ud0a4\ub97c \uad6c\uc6e0\ub294\ub370 \uc190\ub2d8\uc774 \uc601 \uc5c6\ub124...
Output: {{"keywords": ["\ubc84\ud130 \ucfe0\ud0a4"], "weather_signals": []}}

Input: \uc624\ub298 \ube44\ub3c4 \uc624\uace0 \uc601 \ud558\ub298\uc774 \uafb8\ubb3c\uac70\ub9ac\ub294\ub370 \ub9c9\uac78\ub9ac\ub791 \ud30c\uc804\uc774 \ub531\uc774\uaca0\ub2e4
Output: {{"keywords": ["\ub9c9\uac78\ub9ac", "\ud30c\uc804"], "weather_signals": ["\ube44"]}}

Input: \uc624\ub298 \ub538\ub798\ubbf8\uac00 \uc601\uad6d \ube48\ud2f0\uc9c0\uc0f5\uc5d0\uc11c \uace0\uae09 \ucc3b\uc794\uc744 \uac00\uc838\uc640\uc11c \uc9c4\uc5f4\uc7a5\uc5d0 \uc0c8\ub85c \ub460\uc5b4.
Output: {{"keywords": ["\ucc3b\uc794"], "weather_signals": []}}

Input: \uc694\uc998 \uba39\uace0 \uc0b4\uae30 \ub9cc\ub9cc\uce58 \uc54a\ub2e4.. \uadf8\ub798\ub3c4 \uc81c\ucca0 \uc74c\uc2dd\uc740 \uba39\uace0 \uc0b4\uc544\uc57c\uc9c0.. \ubc24\ud638\ubc15\uc774 \uc694\uc998 \uc81c\ucca0\uc774\uc57c.
Output: {{"keywords": ["\ubc24\ud638\ubc15", "\uc81c\ucca0 \uc74c\uc2dd"], "weather_signals": []}}

Input: \ubd04\ubc14\ub78c \uc0b4\ub791\ubd80\ub294 \ub0a0\uc5d0\ub294 \ub538\uae30 \ub77c\ub5bc\ub791 \ubd04 \ub514\uc800\ud2b8 \uc62c\ub9ac\uace0 \uc2f6\ub2e4
Output: {{"keywords": ["\ub538\uae30 \ub77c\ub5bc", "\ubd04 \ub514\uc800\ud2b8"], "weather_signals": ["\ubd04\ubc14\ub78c"]}}

Input: {utterance}
Output:
"""


class KeywordExtractionUnavailableError(RuntimeError):
    """Raised when the local keyword extraction model is unavailable."""


@dataclass
class KeywordExtractionResult:
    keywords: list[str]
    weather_signals: list[str]


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
        self._model: Any = None
        self._lock = threading.Lock()

    async def preload(self) -> None:
        await asyncio.to_thread(self._ensure_model)

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
                keyword_model_loaded=self._model is not None,
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
            raw_output = await asyncio.wait_for(
                asyncio.to_thread(self._generate_keywords, prompt),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            logger.warning(
                "Keyword extraction timed out while waiting for llama-cpp completion.",
                extra=build_log_extra(
                    "keyword_extraction.inference.completed",
                    component="keyword_extraction",
                    stage="inference",
                    outcome="failed",
                    error_type="TimeoutError",
                    keyword_timeout_seconds=self.timeout_seconds,
                    elapsed_ms=int((time.perf_counter() - started_at) * 1000),
                    keyword_model_loaded=self._model is not None,
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
                    keyword_model_loaded=self._model is not None,
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
                keyword_count=len(result.keywords),
                keywords_preview=", ".join(result.keywords),
                weather_signal_count=len(result.weather_signals),
                weather_signals_preview=", ".join(result.weather_signals),
            ),
        )
        return result

    def _ensure_model(self):
        if self._model is not None:
            return self._model

        with self._lock:
            if self._model is not None:
                return self._model

            if not self.enabled:
                raise KeywordExtractionUnavailableError(
                    "Keyword extraction model is disabled."
                )

            ensure_started_at = time.perf_counter()
            try:
                self.model_path = ensure_keyword_model_available(self.model_path)
            except Exception as exc:
                raise KeywordExtractionUnavailableError(str(exc)) from exc

            try:
                from llama_cpp import Llama
            except ImportError as exc:
                try:
                    installed_version = importlib.metadata.version("llama-cpp-python")
                except importlib.metadata.PackageNotFoundError:
                    installed_version = "not installed"
                raise KeywordExtractionUnavailableError(
                    "The official llama-cpp-python runtime is required for "
                    "keyword extraction. "
                    f"Installed version: {installed_version}."
                ) from exc

            try:
                logger.info(
                    "Initializing keyword llama-cpp model.",
                    extra=build_log_extra(
                        "keyword_extraction.model_init.started",
                        component="keyword_extraction",
                        stage="model_init",
                        outcome="started",
                        keyword_model_path=str(self.model_path),
                        keyword_model_ctx_size=self.n_ctx,
                        keyword_model_threads=self.n_threads,
                        keyword_model_gpu_layers=self.n_gpu_layers,
                    ),
                )
                self._model = Llama(
                    model_path=str(self.model_path),
                    n_ctx=self.n_ctx,
                    n_threads=self.n_threads,
                    n_gpu_layers=self.n_gpu_layers,
                    verbose=False,
                )
                logger.info(
                    "Keyword llama-cpp model initialized.",
                    extra=build_log_extra(
                        "keyword_extraction.model_init.completed",
                        component="keyword_extraction",
                        stage="model_init",
                        outcome="succeeded",
                        keyword_model_path=str(self.model_path),
                        elapsed_ms=int(
                            (time.perf_counter() - ensure_started_at) * 1000
                        ),
                    ),
                )
            except Exception as exc:
                logger.warning(
                    "Keyword llama-cpp model initialization failed.",
                    extra=build_log_extra(
                        "keyword_extraction.model_init.completed",
                        component="keyword_extraction",
                        stage="model_init",
                        outcome="failed",
                        error_type=exc.__class__.__name__,
                        keyword_model_path=str(self.model_path),
                        elapsed_ms=int(
                            (time.perf_counter() - ensure_started_at) * 1000
                        ),
                    ),
                    exc_info=True,
                )
                raise KeywordExtractionUnavailableError(
                    f"Failed to initialize keyword model from {self.model_path}."
                ) from exc

        return self._model

    def _generate_keywords(self, prompt: str) -> str:
        model = self._ensure_model()
        generation_started_at = time.perf_counter()

        response_kwargs = {
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return only a JSON object with Korean promotional keywords "
                        'and weather_signals fields.'
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": self.temperature,
            "top_p": self.top_p,
            "max_tokens": self.max_tokens,
        }

        try:
            logger.info(
                "Calling llama-cpp create_chat_completion for keyword extraction.",
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
            response = model.create_chat_completion(
                **response_kwargs,
                response_format={
                    "type": "json_object",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "keywords": {
                                "type": "array",
                                "minItems": 1,
                                "maxItems": 3,
                                "items": {"type": "string"},
                            },
                            "weather_signals": {
                                "type": "array",
                                "maxItems": 3,
                                "items": {"type": "string"},
                            },
                        },
                        "required": ["keywords"],
                    },
                },
            )
        except TypeError:
            logger.info(
                "llama-cpp response_format is unsupported; retrying without schema enforcement."
                ,
                extra=build_log_extra(
                    "keyword_extraction.generate.response_format_retry",
                    component="keyword_extraction",
                    stage="generate",
                    outcome="retrying",
                ),
            )
            response = model.create_chat_completion(**response_kwargs)

        raw_output = (
            response.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        logger.info(
            "llama-cpp keyword completion returned.",
            extra=build_log_extra(
                "keyword_extraction.generate.completed",
                component="keyword_extraction",
                stage="generate",
                outcome="succeeded",
                elapsed_ms=int((time.perf_counter() - generation_started_at) * 1000),
                raw_output_preview=preview_text(
                    raw_output,
                    settings.LOG_EVENT_PREVIEW_MAX_LEN,
                ),
            ),
        )
        return raw_output

    def _parse_extraction_result(self, raw_output: str) -> KeywordExtractionResult:
        payload = self._extract_json_payload(raw_output)

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction returned invalid JSON."
            ) from exc

        weather_payload: list[Any] = []
        if isinstance(parsed, dict):
            weather_candidate = parsed.get("weather_signals")
            if isinstance(weather_candidate, list):
                weather_payload = weather_candidate
            parsed = parsed.get("keywords")

        if not isinstance(parsed, list):
            raise KeywordExtractionUnavailableError(
                "Keyword extraction returned a non-list payload."
            )

        keywords: list[str] = []
        seen_keywords: set[str] = set()

        for item in parsed:
            if not isinstance(item, str):
                continue

            normalized = self._normalize_keyword(item)
            if not normalized or normalized in seen_keywords:
                continue

            seen_keywords.add(normalized)
            keywords.append(normalized)
            if len(keywords) == 3:
                break

        weather_signals: list[str] = []
        seen_weather_signals: set[str] = set()

        for item in weather_payload:
            if not isinstance(item, str):
                continue

            normalized = self._normalize_weather_signal(item)
            if not normalized or normalized in seen_weather_signals:
                continue

            seen_weather_signals.add(normalized)
            weather_signals.append(normalized)
            if len(weather_signals) == 3:
                break

        if not keywords:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction returned no usable keywords."
            )

        logger.info(
            "Keyword extraction parsed keywords.",
            extra=build_log_extra(
                "keyword_extraction.parse.completed",
                component="keyword_extraction",
                stage="parse",
                outcome="succeeded",
                keywords_preview=", ".join(keywords),
                weather_signals_preview=", ".join(weather_signals),
                raw_output_preview=preview_text(
                    raw_output,
                    settings.LOG_EVENT_PREVIEW_MAX_LEN,
                ),
            ),
        )
        return KeywordExtractionResult(
            keywords=keywords,
            weather_signals=weather_signals,
        )

    def _parse_keywords(self, raw_output: str) -> list[str]:
        return self._parse_extraction_result(raw_output).keywords

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

    @staticmethod
    def _normalize_keyword(keyword: str) -> str:
        normalized = keyword.strip().strip("\"'`")
        normalized = re.sub(r"^[\s\W_]+|[\s\W_]+$", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

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

    @staticmethod
    def _normalize_weather_signal(signal: str) -> str:
        normalized = signal.strip().strip("\"'`")
        normalized = re.sub(r"^[\s\W_]+|[\s\W_]+$", "", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        if len(normalized) < 1:
            return ""
        if len(normalized) > 20:
            return ""
        if not any(hint in normalized for hint in _WEATHER_SIGNAL_HINTS):
            return ""
        if not re.search(r"[가-힣A-Za-z]", normalized):
            return ""
        return normalized


def build_keyword_extraction_service() -> KeywordExtractionService:
    return KeywordExtractionService(
        model_path=settings.keyword_model_path,
        enabled=settings.KEYWORD_MODEL_ENABLED,
        n_ctx=settings.KEYWORD_MODEL_CTX_SIZE,
        max_tokens=settings.KEYWORD_MODEL_MAX_TOKENS,
        temperature=settings.KEYWORD_MODEL_TEMPERATURE,
        top_p=settings.KEYWORD_MODEL_TOP_P,
        n_threads=settings.KEYWORD_MODEL_THREADS,
        n_gpu_layers=settings.KEYWORD_MODEL_GPU_LAYERS,
        timeout_seconds=settings.KEYWORD_MODEL_TIMEOUT_SECONDS,
    )


def get_keyword_extraction_service(request: Request) -> KeywordExtractionService:
    service = getattr(request.app.state, "keyword_extraction_service", None)
    if service is None:
        raise RuntimeError("Keyword extraction service is not initialized.")
    return service
