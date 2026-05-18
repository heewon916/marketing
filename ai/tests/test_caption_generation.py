import httpx
import pytest

from app.services.caption_generation import (
    DEFAULT_FALLBACK_GUIDE_TEXT,
    CaptionGenerationRequest,
    CaptionGenerationService,
    CaptionGenerationUnavailableError,
)
from app.services.menu_promotion_context import StoreMenuCandidate


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
        keywords=["막걸리"],
        owner_persona="warm",
        weather_tags=["PRECIP_RAIN"],
    )

    _run_immediate(service.generate_text(request))
    _run_immediate(service.generate_text(request))

    assert calls == [(True, False), (False, False), (False, False)]
    assert service._response_format_supported is False


def test_caption_generation_service_uses_menu_promotion_prompt_only(
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
            content='{"guide_text":"가이드를 확인하세요.","caption":"캡션을 확인하세요."}',
        )

    monkeypatch.setattr(service, "_post_chat_completion", fake_post_chat_completion)

    _run_immediate(
        service.generate_text(
            CaptionGenerationRequest(
                keywords=["keyword"],
                owner_persona="warm",
                weather_tags=["PRECIP_CLEAR"],
            )
        )
    )

    assert len(prompts) == 1
    assert '게시물 목적은 "메뉴 홍보"입니다.' in prompts[0]
    assert "실제로 판매하는 것만 홍보" in prompts[0]
    assert '게시물 목적은 "영업 공지"입니다.' not in prompts[0]
    assert '게시물 목적은 "일상 공유"입니다.' not in prompts[0]


def test_caption_generation_service_uses_korean_fallback_guide_text() -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")

    fallback_result = service.build_fallback_result(
        CaptionGenerationRequest(
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

    prompt = service._pipeline.build_prompt(
        CaptionGenerationRequest(
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
    assert "문장을 그대로 복사하지 말고" in prompt


def test_caption_generation_prompt_includes_menu_candidates() -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")

    prompt = service._pipeline.build_prompt(
        CaptionGenerationRequest(
            keywords=["막걸리", "파전"],
            owner_persona="warm",
            weather_tags=["PRECIP_RAIN"],
            menu_candidates=[
                StoreMenuCandidate(
                    id="1",
                    name="해물파전",
                    price=18000,
                    description="비 오는 날 잘 나가는 대표 메뉴",
                    weather_tags=["PRECIP_RAIN"],
                    matched_weather_tags=["PRECIP_RAIN"],
                )
            ],
        )
    )

    assert "selected_menu_name" in prompt
    assert "메뉴 후보 목록" in prompt
    assert "메뉴명: 해물파전" in prompt
    assert "일치한 weather_tags: PRECIP_RAIN" in prompt


def test_caption_generation_service_parses_selected_menu_name_from_candidates() -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    candidates = [
        StoreMenuCandidate(
            id="1",
            name="해물파전",
            price=18000,
            description="비 오는 날 잘 나가는 대표 메뉴",
            weather_tags=["PRECIP_RAIN"],
            matched_weather_tags=["PRECIP_RAIN"],
        )
    ]

    result = service._parse_generation_result(
        '{"guide_text":"해물파전이 잘 보이도록 접시를 가까이 담아보세요.","caption":"비 오는 날엔 막걸리와 잘 어울리는 해물파전을 따뜻하게 소개해보세요.","selected_menu_name":"해물파전"}',
        menu_candidates=candidates,
    )

    assert result.selected_menu_name == "해물파전"


def test_caption_generation_service_rejects_selected_menu_outside_candidates() -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    candidates = [
        StoreMenuCandidate(
            id="1",
            name="해물파전",
            price=18000,
            description="비 오는 날 잘 나가는 대표 메뉴",
            weather_tags=["PRECIP_RAIN"],
            matched_weather_tags=["PRECIP_RAIN"],
        )
    ]

    with pytest.raises(
        CaptionGenerationUnavailableError,
        match="outside the provided candidates",
    ):
        service._parse_generation_result(
            '{"guide_text":"메뉴를 가까이 담아보세요.","caption":"오늘은 국물이 좋은 수프를 소개해보세요.","selected_menu_name":"오늘의 수프"}',
            menu_candidates=candidates,
        )


def test_caption_generation_fallback_prefers_first_menu_candidate() -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")

    fallback_result = service.build_fallback_result(
        CaptionGenerationRequest(
            keywords=["막걸리"],
            owner_persona="warm",
            weather_tags=["PRECIP_RAIN"],
            menu_candidates=[
                StoreMenuCandidate(
                    id="1",
                    name="해물파전",
                    price=18000,
                    description="비 오는 날 잘 나가는 대표 메뉴",
                    weather_tags=["PRECIP_RAIN"],
                    matched_weather_tags=["PRECIP_RAIN"],
                )
            ],
        ),
        fallback_source="caption_model_fallback",
    )

    assert fallback_result.result.selected_menu_name == "해물파전"
    assert "해물파전" in fallback_result.result.guide_text
    assert "해물파전" in fallback_result.result.draft_caption
