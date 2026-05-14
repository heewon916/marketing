import httpx

import pytest

from app.services.keyword_extraction import (
    KeywordExtractionService,
    KeywordExtractionUnavailableError,
)
from tests.utils.session_support import _make_chat_response, _run_immediate


def test_keyword_extraction_service_normalizes_and_limits_keywords() -> None:
    service = KeywordExtractionService()

    keywords = service._parse_keywords(
        "["
        '"\\ub9c9\\uac78\\ub9ac", '
        '" \\ud30c\\uc804 ", '
        '"\\ub9c9\\uac78\\ub9ac", '
        '"\\uc624\\ub298", '
        '"\\ucc3b\\uc794", '
        '"\\ub514\\uc800\\ud2b8"'
        "]"
    )

    assert keywords == ["\ub9c9\uac78\ub9ac", "\ud30c\uc804", "\ucc3b\uc794"]


def test_keyword_extraction_service_strips_particles_from_keywords() -> None:
    service = KeywordExtractionService()

    assert service._normalize_keyword("\ubc24\ud638\ubc15\uc774") == "\ubc24\ud638\ubc15"
    assert (
        service._normalize_keyword("\uc81c\ucca0 \uc74c\uc2dd\uc740")
        == "\uc81c\ucca0 \uc74c\uc2dd"
    )


def test_keyword_extraction_service_rejects_sentence_like_keywords() -> None:
    service = KeywordExtractionService()

    assert service._normalize_keyword("\uba39\uace0 \uc0b4\uc544\uc57c\uc9c0") == ""
    assert service._normalize_keyword("\uc81c\ucca0\uc774\uc57c") == ""


def test_keyword_extraction_service_parses_purpose_and_keywords() -> None:
    service = KeywordExtractionService()

    result = service._parse_extraction_result(
        "{"
        '"purpose": "\\uba54\\ub274 \\ud64d\\ubcf4", '
        '"keywords": ['
        '"\\ubc24\\ud638\\ubc15", '
        '"\\uc81c\\ucca0 \\uc74c\\uc2dd", '
        '"\\ub9e4\\uc7a5"'
        "]"
        "}"
    )

    assert result.purpose == "\uba54\ub274 \ud64d\ubcf4"
    assert result.draft_keywords == ["\ubc24\ud638\ubc15", "\uc81c\ucca0 \uc74c\uc2dd"]
    assert result.final_keywords == []


def test_keyword_extraction_service_rejects_invalid_purpose() -> None:
    service = KeywordExtractionService()

    with pytest.raises(KeywordExtractionUnavailableError, match="invalid purpose"):
        service._parse_extraction_result(
            '{'
            '"purpose": "\\uae30\\ud0c0", '
            '"keywords": ["\\ub9c9\\uac78\\ub9ac"]'
            "}"
        )


def test_keyword_extraction_service_raises_when_disabled() -> None:
    service = KeywordExtractionService(enabled=False)

    with pytest.raises(KeywordExtractionUnavailableError):
        _run_immediate(
            service.extract_keywords(
                "\uc624\ub298 \ub9c9\uac78\ub9ac\ub791 \ud30c\uc804\uc774 \ub531\uc774\ub2e4"
            )
        )


def test_keyword_extraction_service_calls_remote_server_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(base_url="http://llama-server:8000")
    calls: list[bool] = []

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        calls.append(include_response_format)
        return _make_chat_response(
            200,
            content='{"purpose":"\\uba54\\ub274 \\ud64d\\ubcf4","keywords":["\\ub9c9\\uac78\\ub9ac"]}',
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    result = _run_immediate(
        service.extract_keywords(
            "\uc624\ub298 \ube44\uc640\uc11c \ub9c9\uac78\ub9ac\uac00 \ub561\uae34\ub2e4"
        )
    )

    assert calls == [True]
    assert result.purpose == "\uba54\ub274 \ud64d\ubcf4"
    assert result.draft_keywords == ["\ub9c9\uac78\ub9ac"]


def test_keyword_extraction_service_retries_without_response_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(base_url="http://llama-server:8000")
    calls: list[bool] = []

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        calls.append(include_response_format)
        if include_response_format:
            return httpx.Response(
                400,
                request=httpx.Request(
                    "POST",
                    "http://llama-server:8000/v1/chat/completions",
                ),
                text="response_format is unsupported",
            )
        return _make_chat_response(
            200,
            content='{"purpose":"\\uba54\\ub274 \\ud64d\\ubcf4","keywords":["\\ud30c\\uc804"]}',
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    result = _run_immediate(
        service.extract_keywords(
            "\uc624\ub298\uc740 \ud30c\uc804\uc774 \uc798 \ub098\uac08 \uac83 \uac19\ub2e4"
        )
    )

    assert calls == [True, False]
    assert result.draft_keywords == ["\ud30c\uc804"]


def test_keyword_extraction_service_raises_on_remote_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(base_url="http://llama-server:8000")

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        raise httpx.ReadTimeout("timed out")

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    with pytest.raises(KeywordExtractionUnavailableError, match="timed out"):
        _run_immediate(
            service.extract_keywords(
                "\uc624\ub298 \ub9c9\uac78\ub9ac\uac00 \ub561\uae34\ub2e4"
            )
        )


def test_keyword_extraction_service_preload_uses_health_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = KeywordExtractionService(
        base_url="http://llama-server:8000",
        health_endpoint="/health",
    )
    calls: list[str] = []

    class RecordingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str) -> httpx.Response:
            calls.append(url)
            return httpx.Response(200, request=httpx.Request("GET", url), text="ok")

    monkeypatch.setattr(
        "app.services.keyword_extraction.httpx.AsyncClient",
        RecordingAsyncClient,
    )

    _run_immediate(service.preload())

    assert calls == ["http://llama-server:8000/health"]
