from __future__ import annotations

import asyncio
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
from app.keyword_model_download import ensure_keyword_model_available

logger = logging.getLogger(__name__)

_GENERIC_KEYWORDS = {
    "\uc624\ub298",
    "\uc190\ub2d8",
    "\ub9e4\uc7a5",
    "\uac00\uac8c",
    "\ubd84\uc704\uae30",
    "\uae30\ubd84",
    "\ud558\ub298",
    "\ub0a0\uc528",
    "\uc0c1\ud669",
    "\uc9c4\uc5f4\uc7a5",
}

_PROMPT_TEMPLATE = """You extract 1 to 3 Korean promotional keywords from a user utterance.

Rules:
- Return JSON array text only.
- Return 1 to 3 items.
- Select only concrete menu, food, drink, product, prop, or object nouns.
- Exclude weather, mood, abstract descriptions, and general situation words.
- Preserve useful noun phrases.
- Keep output deduplicated.

Examples:
Input: \uc624\ub298 \uc544\uc8fc \ube44\uc2fc \ubc14\ub2d0\ub77c\ub85c \ubc84\ud130 \ucfe0\ud0a4\ub97c \uad6c\uc6e0\ub294\ub370 \uc190\ub2d8\uc774 \uc601 \uc5c6\ub124...
Output: ["\ubc84\ud130 \ucfe0\ud0a4"]

Input: \uc624\ub298 \ube44\ub3c4 \uc624\uace0 \uc601 \ud558\ub298\uc774 \uafb8\ubb3c\uac70\ub9ac\ub294\ub370 \ub9c9\uac78\ub9ac\ub791 \ud30c\uc804\uc774 \ub531\uc774\uaca0\ub2e4
Output: ["\ub9c9\uac78\ub9ac", "\ud30c\uc804"]

Input: \uc624\ub298 \ub538\ub798\ubbf8\uac00 \uc601\uad6d \ube48\ud2f0\uc9c0\uc0f5\uc5d0\uc11c \uace0\uae09 \ucc3b\uc794\uc744 \uac00\uc838\uc640\uc11c \uc9c4\uc5f4\uc7a5\uc5d0 \uc0c8\ub85c \ub460\uc5b4.
Output: ["\ucc3b\uc794"]

Input: {utterance}
Output:
"""


class KeywordExtractionUnavailableError(RuntimeError):
    """Raised when the local keyword extraction model is unavailable."""


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

    async def extract_keywords(self, utterance: str) -> list[str]:
        if not self.enabled:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction model is disabled."
            )

        prompt = _PROMPT_TEMPLATE.format(utterance=utterance.strip())
        started_at = time.perf_counter()

        logger.info(
            "Keyword extraction inference started.",
            extra={
                "keyword_timeout_seconds": self.timeout_seconds,
                "keyword_model_loaded": self._model is not None,
                "utterance_length": len(utterance),
            },
        )

        try:
            raw_output = await asyncio.wait_for(
                asyncio.to_thread(self._generate_keywords, prompt),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            logger.warning(
                "Keyword extraction timed out while waiting for llama-cpp completion.",
                extra={
                    "keyword_timeout_seconds": self.timeout_seconds,
                    "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
                    "keyword_model_loaded": self._model is not None,
                },
            )
            raise KeywordExtractionUnavailableError(
                "Keyword extraction timed out."
            ) from exc
        except KeywordExtractionUnavailableError:
            raise
        except Exception as exc:
            logger.warning(
                "Keyword extraction inference raised an unexpected exception.",
                extra={
                    "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
                    "keyword_model_loaded": self._model is not None,
                },
                exc_info=True,
            )
            raise KeywordExtractionUnavailableError(
                "Keyword extraction inference failed."
            ) from exc

        keywords = self._parse_keywords(raw_output)
        logger.info(
            "Keyword extraction inference finished.",
            extra={
                "elapsed_ms": int((time.perf_counter() - started_at) * 1000),
                "keywords_preview": ", ".join(keywords),
            },
        )
        return keywords

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
                    extra={
                        "keyword_model_path": str(self.model_path),
                        "keyword_model_ctx_size": self.n_ctx,
                        "keyword_model_threads": self.n_threads,
                        "keyword_model_gpu_layers": self.n_gpu_layers,
                    },
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
                    extra={
                        "keyword_model_path": str(self.model_path),
                        "elapsed_ms": int(
                            (time.perf_counter() - ensure_started_at) * 1000
                        ),
                    },
                )
            except Exception as exc:
                logger.warning(
                    "Keyword llama-cpp model initialization failed.",
                    extra={
                        "keyword_model_path": str(self.model_path),
                        "elapsed_ms": int(
                            (time.perf_counter() - ensure_started_at) * 1000
                        ),
                    },
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
                    "content": "Return only a JSON array of 1 to 3 Korean keywords.",
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
                extra={
                    "keyword_max_tokens": self.max_tokens,
                    "keyword_temperature": self.temperature,
                    "keyword_top_p": self.top_p,
                },
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
                            }
                        },
                        "required": ["keywords"],
                    },
                },
            )
        except TypeError:
            logger.info(
                "llama-cpp response_format is unsupported; retrying without schema enforcement."
            )
            response = model.create_chat_completion(**response_kwargs)

        raw_output = (
            response.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        logger.info(
            "llama-cpp keyword completion returned.",
            extra={
                "elapsed_ms": int((time.perf_counter() - generation_started_at) * 1000),
                "raw_output_preview": raw_output[:200],
            },
        )
        return raw_output

    def _parse_keywords(self, raw_output: str) -> list[str]:
        payload = self._extract_json_payload(raw_output)

        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction returned invalid JSON."
            ) from exc

        if isinstance(parsed, dict) and isinstance(parsed.get("keywords"), list):
            parsed = parsed["keywords"]
        if not isinstance(parsed, list):
            raise KeywordExtractionUnavailableError(
                "Keyword extraction returned a non-list payload."
            )

        keywords: list[str] = []
        seen: set[str] = set()

        for item in parsed:
            if not isinstance(item, str):
                continue

            normalized = self._normalize_keyword(item)
            if not normalized or normalized in seen:
                continue

            seen.add(normalized)
            keywords.append(normalized)
            if len(keywords) == 3:
                break

        if not keywords:
            raise KeywordExtractionUnavailableError(
                "Keyword extraction returned no usable keywords."
            )

        logger.info(
            "Keyword extraction parsed keywords.",
            extra={
                "keywords_preview": ", ".join(keywords),
                "raw_output_preview": raw_output[:200],
            },
        )
        return keywords

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
        if normalized in _GENERIC_KEYWORDS:
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
