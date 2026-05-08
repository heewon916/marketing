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
                '"caption":"오늘의 시그니처 메뉴를 소개합니다."}'
            ),
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    result = _run_immediate(
        service.generate_text(
            CaptionGenerationRequest(
                purpose="메뉴 홍보",
                keywords=["signature menu"],
                owner_persona="aesthetic",
                weather_tags=["PRECIP_CLEAR"],
            )
        )
    )

    assert calls == [True]
    assert result.guide_text == "메뉴가 잘 보이게 촬영해보세요."
    assert result.draft_caption == "오늘의 시그니처 메뉴를 소개합니다."
    assert result.stored_caption == result.draft_caption

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
                '"caption":"비 오는 날 어울리는 메뉴를 소개합니다."}'
            ),
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    result = _run_immediate(
        service.generate_text(
            CaptionGenerationRequest(
                purpose="메뉴 홍보",
                keywords=["막걸리"],
                owner_persona="warm",
                weather_tags=["PRECIP_RAIN"],
            )
        )
    )

    assert calls == [True, False]
    assert result.draft_caption == "비 오는 날 어울리는 메뉴를 소개합니다."


def test_caption_generation_service_does_not_retry_on_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    calls: list[bool] = []

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        calls.append(include_response_format)
        return httpx.Response(
            400,
            request=httpx.Request(
                "POST",
                "http://caption-server:8002/v1/chat/completions",
            ),
            text="schema validation failed: caption is required",
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    with pytest.raises(CaptionGenerationUnavailableError, match="HTTP 400"):
        _run_immediate(
            service.generate_text(
                CaptionGenerationRequest(
                    purpose="메뉴 홍보",
                    keywords=["막걸리"],
                    owner_persona="warm",
                    weather_tags=["PRECIP_RAIN"],
                )
            )
        )

    assert calls == [True]
    assert service._response_format_supported is True


def test_caption_generation_service_caches_response_format_unsupported(
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
                '{"guide_text":"가이드.","caption":"캡션."}'
            ),
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    request = CaptionGenerationRequest(
        purpose="메뉴 홍보",
        keywords=["막걸리"],
        owner_persona="warm",
        weather_tags=["PRECIP_RAIN"],
    )

    _run_immediate(service.generate_text(request))
    _run_immediate(service.generate_text(request))

    assert calls == [True, False, False]
    assert service._response_format_supported is False


def test_caption_generation_service_selects_prompt_by_purpose(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    prompts: list[str] = []

    async def fake_post_chat_completion(prompt: str, *, include_response_format: bool):
        prompts.append(prompt)
        return _make_chat_response(
            200,
            content=(
                '{"guide_text":"가이드를 확인하세요.",'
                '"caption":"캡션을 확인하세요."}'
            ),
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    for purpose in ("메뉴 홍보", "영업 공지", "일상 공유"):
        _run_immediate(
            service.generate_text(
                CaptionGenerationRequest(
                    purpose=purpose,
                    keywords=["keyword"],
                    owner_persona="warm",
                    weather_tags=["PRECIP_CLEAR"],
                )
            )
        )

    assert '게시물 목적은 "메뉴 홍보"입니다.' in prompts[0]
    assert "메뉴, 상품, 재료, 또는 매장에서 제공하는 것을 홍보하는 톤" in prompts[0]
    assert '게시물 목적은 "영업 공지"입니다.' in prompts[1]
    assert "영업, 일정, 운영 가능 여부에 대한 명확한 영업 공지 톤" in prompts[1]
    assert '게시물 목적은 "일상 공유"입니다.' in prompts[2]
    assert "사장님의 일상, 매장 분위기, 비하인드 순간을 공유하는 톤" in prompts[2]


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
