from __future__ import annotations

from typing import Any

import httpx


class RemoteModelClient:
    def __init__(
        self,
        *,
        base_url: str,
        chat_endpoint: str,
        health_endpoint: str,
        api_key: str | None,
        timeout_seconds: float,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.chat_endpoint = chat_endpoint
        self.health_endpoint = health_endpoint
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @property
    def chat_url(self) -> str:
        return f"{self.base_url}{self.chat_endpoint}"

    @property
    def health_url(self) -> str:
        return f"{self.base_url}{self.health_endpoint}"

    def build_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def post_chat_completion(self, payload: dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            return await client.post(
                self.chat_url,
                headers=self.build_headers(),
                json=payload,
            )

    async def check_health(self) -> httpx.Response:
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(self.health_url)
        response.raise_for_status()
        return response

    @staticmethod
    def extract_message_content(response: httpx.Response) -> str:
        response_payload = response.json()
        content = (
            response_payload.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if isinstance(content, list):
            text_parts = [
                str(part.get("text", ""))
                for part in content
                if isinstance(part, dict) and part.get("type") == "text"
            ]
            return "".join(text_parts)
        return content if isinstance(content, str) else ""
