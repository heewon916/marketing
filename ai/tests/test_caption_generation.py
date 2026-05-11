import httpx
import pytest

from app.services.caption_generation import (
    DEFAULT_FALLBACK_GUIDE_TEXT,
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
    calls: list[tuple[bool, bool]] = []

    async def fake_post_chat_completion(
        prompt: str,
        *,
        include_response_format: bool,
        strict_language: bool,
    ):
        calls.append((include_response_format, strict_language))
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

    assert calls == [(True, False)]
    assert result.guide_text == "메뉴가 잘 보이게 촬영해보세요."
    assert result.draft_caption == "오늘의 시그니처 메뉴를 소개합니다."
    assert result.stored_caption == result.draft_caption


def test_caption_generation_service_retries_without_response_format(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    calls: list[tuple[bool, bool]] = []

    async def fake_post_chat_completion(
        prompt: str,
        *,
        include_response_format: bool,
        strict_language: bool,
    ):
        calls.append((include_response_format, strict_language))
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

    assert calls == [(True, False), (False, False)]
    assert result.draft_caption == "비 오는 날 어울리는 메뉴를 소개합니다."


def test_caption_generation_service_does_not_retry_on_validation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    calls: list[tuple[bool, bool]] = []

    async def fake_post_chat_completion(
        prompt: str,
        *,
        include_response_format: bool,
        strict_language: bool,
    ):
        calls.append((include_response_format, strict_language))
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

    assert calls == [(True, False)]
    assert service._response_format_supported is True


def test_caption_generation_service_caches_response_format_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    calls: list[tuple[bool, bool]] = []

    async def fake_post_chat_completion(
        prompt: str,
        *,
        include_response_format: bool,
        strict_language: bool,
    ):
        calls.append((include_response_format, strict_language))
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
            content='{"guide_text":"가이드.","caption":"캡션."}',
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

    assert calls == [(True, False), (False, False), (False, False)]
    assert service._response_format_supported is False


def test_caption_generation_service_selects_prompt_by_purpose(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    prompts: list[str] = []

    async def fake_post_chat_completion(
        prompt: str,
        *,
        include_response_format: bool,
        strict_language: bool,
    ):
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


def test_caption_generation_service_uses_korean_fallback_guide_text() -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")

    fallback_result = service.build_fallback_result(
        CaptionGenerationRequest(
            purpose="메뉴 홍보",
            keywords=["signature menu"],
            owner_persona="aesthetic",
            weather_tags=[],
        ),
        fallback_source="caption_model_fallback",
    )

    assert fallback_result.result.guide_text != DEFAULT_FALLBACK_GUIDE_TEXT
    assert "사장님" in fallback_result.result.guide_text
    assert "Make sure" not in fallback_result.result.guide_text


def test_caption_generation_service_retries_with_stricter_korean_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    calls: list[tuple[bool, bool]] = []

    async def fake_post_chat_completion(
        prompt: str,
        *,
        include_response_format: bool,
        strict_language: bool,
    ):
        calls.append((include_response_format, strict_language))
        if len(calls) == 1:
            return _make_chat_response(
                200,
                content=(
                    '{"guide_text":"Show the signature menu clearly.",'
                    '"caption":"Fresh pasta for tonight."}'
                ),
            )
        return _make_chat_response(
            200,
            content=(
                '{"guide_text":"시그니처 메뉴가 잘 보이도록 촬영해보세요.",'
                '"caption":"오늘의 시그니처 메뉴를 따뜻하게 소개해보세요."}'
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

    assert calls == [(True, False), (True, True)]
    assert result.guide_text == "시그니처 메뉴가 잘 보이도록 촬영해보세요."


def test_caption_generation_service_raises_when_retry_still_non_korean(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    calls: list[tuple[bool, bool]] = []

    async def fake_post_chat_completion(
        prompt: str,
        *,
        include_response_format: bool,
        strict_language: bool,
    ):
        calls.append((include_response_format, strict_language))
        return _make_chat_response(
            200,
            content=(
                '{"guide_text":"Show the dish clearly.",'
                '"caption":"Fresh soup for today."}'
            ),
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    with pytest.raises(
        CaptionGenerationUnavailableError,
        match="not sufficiently Korean",
    ):
        _run_immediate(
            service.generate_text(
                CaptionGenerationRequest(
                    purpose="메뉴 홍보",
                    keywords=["seasonal soup"],
                    owner_persona="warm",
                    weather_tags=["PRECIP_RAIN"],
                )
            )
        )

    assert calls == [(True, False), (True, True)]


def test_caption_generation_service_rejects_mixed_non_korean_output() -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")

    with pytest.raises(
        CaptionGenerationUnavailableError,
        match="not sufficiently Korean",
    ):
        service._parse_generation_result(
            '{"guide_text":"메뉴 shot", "caption":"Fresh soup today"}'
        )


def test_caption_generation_service_handles_response_format_retry_before_language_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    calls: list[tuple[bool, bool]] = []

    async def fake_post_chat_completion(
        prompt: str,
        *,
        include_response_format: bool,
        strict_language: bool,
    ):
        calls.append((include_response_format, strict_language))
        if calls == [(True, False)]:
            return httpx.Response(
                400,
                request=httpx.Request(
                    "POST",
                    "http://caption-server:8002/v1/chat/completions",
                ),
                text="response_format unsupported",
            )
        if calls == [(True, False), (False, False)]:
            return _make_chat_response(
                200,
                content=(
                    '{"guide_text":"Show the soup clearly.",'
                    '"caption":"Fresh soup today."}'
                ),
            )
        return _make_chat_response(
            200,
            content=(
                '{"guide_text":"수프가 잘 보이도록 촬영해보세요.",'
                '"caption":"오늘의 수프를 따뜻하게 소개해보세요."}'
            ),
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    result = _run_immediate(
        service.generate_text(
            CaptionGenerationRequest(
                purpose="메뉴 홍보",
                keywords=["soup"],
                owner_persona="warm",
                weather_tags=["PRECIP_RAIN"],
            )
        )
    )

    assert calls == [(True, False), (False, False), (False, True)]
    assert result.draft_caption == "오늘의 수프를 따뜻하게 소개해보세요."


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


def test_caption_generation_prompt_includes_reference_captions() -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")

    prompt = service._get_pipeline("메뉴 홍보").build_prompt(
        CaptionGenerationRequest(
            purpose="메뉴 홍보",
            keywords=["signature menu"],
            owner_persona="aesthetic",
            weather_tags=["PRECIP_CLEAR"],
            reference_captions=[
                "첫 번째 레퍼런스 캡션",
                "두 번째 레퍼런스 캡션",
            ],
        )
    )

    assert "참고용 레퍼런스 캡션" in prompt
    assert "1. 첫 번째 레퍼런스 캡션" in prompt
    assert "2. 두 번째 레퍼런스 캡션" in prompt
    assert "문장을 그대로 복사" in prompt
