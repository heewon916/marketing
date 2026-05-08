import httpx
import pytest

from app.services.caption_generation import (
    CaptionGenerationRequest,
    CaptionGenerationService,
    CaptionGenerationUnavailableError,
)


def _make_chat_response(
    status_code: int,
    *,
    content: str = "",
    url: str = "http://caption-server:8002/v1/chat/completions",
) -> httpx.Response:
    return httpx.Response(
        status_code,
        request=httpx.Request("POST", url),
        json={"choices": [{"message": {"content": content}}]},
    )


def _run_immediate(awaitable):
    iterator = awaitable.__await__()
    try:
        yielded = next(iterator)
    except StopIteration as exc:
        return exc.value

    while True:
        try:
            if hasattr(yielded, "__await__"):
                yielded = iterator.send(_run_immediate(yielded))
            else:
                yielded = iterator.send(None)
        except StopIteration as exc:
            return exc.value


def test_caption_generation_service_calls_remote_server_successfully(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    calls: list[bool] = []

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        calls.append(include_response_format)
        return _make_chat_response(
            200,
            content=(
                '{"guide_text":"메뉴가 잘 보이게 촬영해보세요.",'
                '"caption":"오늘의 시그니처 메뉴를 소개합니다.",'
                '"hashtags":["#시그니처메뉴","#매장추천"]}'
            ),
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    result = _run_immediate(
        service.generate_text(
            CaptionGenerationRequest(
                purpose="메뉴 홍보",
                keywords=["signature menu"],
                owner_persona="aesthetic",
                cloud_cover="clear",
                weather_tags=["PRECIP_CLEAR"],
            )
        )
    )

    assert calls == [True]
    assert result.guide_text == "메뉴가 잘 보이게 촬영해보세요."
    assert result.draft_caption == "오늘의 시그니처 메뉴를 소개합니다."
    assert result.draft_hashtags == ["#시그니처메뉴", "#매장추천"]
    assert "#시그니처메뉴" in result.stored_caption

def test_caption_generation_service_retries_without_response_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    calls: list[bool] = []

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        calls.append(include_response_format)
        if include_response_format:
            return httpx.Response(
                400,
                request=httpx.Request(
                    "POST",
                    "http://caption-server:8002/v1/chat/completions",
                ),
                text="response_format unsupported",
            )
        return _make_chat_response(
            200,
            content=(
                '{"guide_text":"촬영 포인트를 강조해보세요.",'
                '"caption":"비 오는 날 어울리는 메뉴를 소개합니다.",'
                '"hashtags":["비오는날","막걸리"]}'
            ),
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    result = _run_immediate(
        service.generate_text(
            CaptionGenerationRequest(
                purpose="메뉴 홍보",
                keywords=["막걸리"],
                owner_persona="warm",
                cloud_cover="rainy",
                weather_tags=["PRECIP_RAIN"],
            )
        )
    )

    assert calls == [True, False]
    assert result.draft_hashtags == ["#비오는날", "#막걸리"]


def test_caption_generation_service_preload_raises_when_server_unreachable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")

    class FailingAsyncClient:
        def __init__(self, *args, **kwargs) -> None:
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def get(self, url: str) -> httpx.Response:
            raise httpx.ConnectError("connection refused")

    monkeypatch.setattr(
        "app.services.caption_generation.httpx.AsyncClient",
        FailingAsyncClient,
    )

    with pytest.raises(
        CaptionGenerationUnavailableError,
        match="connectivity check failed",
    ):
        _run_immediate(service.preload())
