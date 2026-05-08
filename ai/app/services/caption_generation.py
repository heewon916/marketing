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

logger = logging.getLogger(__name__)

_PROMPT_TEMPLATE = """You generate short Korean Instagram marketing copy for a small shop owner.

Rules:
- Return JSON object text only.
- Use this schema: {{"guide_text": "...", "caption": "...", "hashtags": ["#..."]}}.
- "guide_text" should be 1 to 2 Korean sentences telling the owner what to emphasize in the photo.
- "caption" should be a warm Korean Instagram caption of 1 to 3 short sentences.
- "hashtags" should contain 1 to 5 concise hashtags including the leading # symbol.
- Use the provided keywords naturally. Do not invent unrelated products.
- Keep the output suitable for an Instagram post by a local store owner.

Input:
- owner_persona: {owner_persona}
- weather: {cloud_cover}
- keywords: {keywords}
- weather_tags: {weather_tags}
"""


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

    async def preload(self) -> None:
        await self._check_server_connection()

    async def generate_text(
        self,
        *,
        keywords: list[str],
        owner_persona: str,
        cloud_cover: str,
        weather_tags: list[str],
    ) -> CaptionGenerationResult:
        if not self.enabled:
            raise CaptionGenerationUnavailableError(
                "Caption generation model is disabled."
            )

        prompt = _PROMPT_TEMPLATE.format(
            owner_persona=owner_persona.strip(),
            cloud_cover=cloud_cover.strip(),
            keywords=", ".join(keywords) if keywords else "none",
            weather_tags=", ".join(weather_tags) if weather_tags else "none",
        )
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
                caption_keyword_count=len(keywords),
                caption_keywords_preview=", ".join(keywords[:3]),
                owner_persona=owner_persona,
            ),
        )

        try:
            raw_output = await self._generate(prompt)
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
            ),
        )
        return result

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

    async def _generate(self, prompt: str) -> str:
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
