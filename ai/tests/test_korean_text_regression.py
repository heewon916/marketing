from app.api.routes.sessions import router
from app.services.caption_generation import (
    DEFAULT_FALLBACK_GUIDE_TEXT,
    CaptionGenerationRequest,
    CaptionGenerationService,
)
from app.services.sessions import (
    HEALTH_CHECK_FAILURE_CAPTION,
    HEALTH_CHECK_FAILURE_GUIDE_TEXT,
)


def test_runtime_korean_texts_do_not_contain_mojibake_patterns() -> None:
    service = CaptionGenerationService(base_url="http://caption-server:8002")
    menu_prompt = service._pipeline.build_prompt(
        CaptionGenerationRequest(
            keywords=["해물파전"],
            owner_persona="warm",
            weather_tags=["PRECIP_RAIN"],
        )
    )
    route_summaries = [
        route.summary
        for route in router.routes
        if getattr(route, "summary", None)
    ]
    user_visible_texts = [
        HEALTH_CHECK_FAILURE_GUIDE_TEXT,
        HEALTH_CHECK_FAILURE_CAPTION,
        DEFAULT_FALLBACK_GUIDE_TEXT,
        menu_prompt,
        *route_summaries,
    ]
    mojibake_markers = [
        "?醫롫뻻",
        "筌왖",
        "媛寃뚯쓽",
        "硫붾돱媛",
        "??蹂댁씠",
        "??슦媛",
        "留묒? ??",
        "\ufffd",
    ]

    for text in user_visible_texts:
        for marker in mojibake_markers:
            assert marker not in text
