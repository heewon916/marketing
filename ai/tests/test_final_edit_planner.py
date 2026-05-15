import pytest

from app.services.final_edit_planner import (
    FinalEditPlannerClient,
    FinalEditPlanningError,
    FinalEditSessionContext,
    build_final_edit_prompt,
    load_final_edit_session_context,
    parse_image_edit_plans,
)
from app.services.sessions import session_key


def _planner_client() -> FinalEditPlannerClient:
    return FinalEditPlannerClient(
        model_settings=type(
            "Settings",
            (),
            {
                "base_url": "http://planner.test",
                "chat_endpoint": "/v1/chat/completions",
                "health_endpoint": "/health",
                "api_key": None,
                "timeout_seconds": 30.0,
                "max_tokens": 1024,
                "temperature": 0.2,
                "top_p": 0.9,
                "enabled": True,
            },
        )(),
        model_name="test-model",
    )


@pytest.mark.asyncio
async def test_load_final_edit_session_context_uses_draft_keywords(
    fake_redis_async,
) -> None:
    await fake_redis_async.hset(
        session_key("sess-1"),
        mapping={
            "caption": "포근한 디저트 소개",
            "draft_keyword:2": "따뜻한 분위기",
            "draft_keyword:1": "시그니처 케이크",
            "final_keyword:1": "1001:케이크",
        },
    )

    context = await load_final_edit_session_context(fake_redis_async, "sess-1")

    assert context.caption == "포근한 디저트 소개"
    assert context.keywords == ["시그니처 케이크", "따뜻한 분위기"]


@pytest.mark.asyncio
async def test_load_final_edit_session_context_falls_back_to_final_keywords(
    fake_redis_async,
) -> None:
    await fake_redis_async.hset(
        session_key("sess-2"),
        mapping={
            "caption": "매장 분위기 소개",
            "final_keyword:2": "2002:테이블",
            "final_keyword:1": "1001:케이크",
        },
    )

    context = await load_final_edit_session_context(fake_redis_async, "sess-2")

    assert context.keywords == ["케이크", "테이블"]


def test_build_final_edit_prompt_includes_caption_and_keywords() -> None:
    prompt = build_final_edit_prompt(
        FinalEditSessionContext(
            caption="포근한 케이크 소개",
            keywords=["시그니처 케이크", "크림 디저트"],
        ),
        3,
    )

    assert "[caption] 포근한 케이크 소개" in prompt
    assert "[keywords] 시그니처 케이크, 크림 디저트" in prompt
    assert "color_grading" in prompt
    assert "all 3 input images" in prompt
    assert "image_index from 0 to 2" in prompt


def test_parse_image_edit_plans_rejects_unsupported_tool() -> None:
    with pytest.raises(FinalEditPlanningError, match="Unsupported tool"):
        parse_image_edit_plans(
            """
            [
              {
                "image_index": 0,
                "content": "cake",
                "strategy": "remove object",
                "tools": ["object_removal"],
                "params": {"object_removal": {"target": "logo"}}
              }
            ]
            """
        )


@pytest.mark.asyncio
async def test_final_edit_planner_client_builds_validated_plans() -> None:
    client = _planner_client()

    async def fake_request_plan(image_paths, context):
        assert image_paths == ["a.jpg", "b.jpg"]
        assert context.caption == "포근한 디저트 소개"
        return """
        [
          {
            "image_index": 0,
            "content": "시그니처 케이크가 보인다.",
            "strategy": "노이즈를 줄이고 밝기를 높인다.",
            "tools": ["denoise", "color_grading"],
            "params": {
              "denoise": {"strength": 0.4},
              "color_grading": {"temperature": "warm", "saturation": 0.1, "brightness": 0.1}
            }
          }
        ]
        """

    client._request_plan = fake_request_plan  # type: ignore[method-assign]

    plans = await client.build_plans(
        ["a.jpg", "b.jpg"],
        FinalEditSessionContext(caption="포근한 디저트 소개", keywords=["케이크"]),
    )

    assert len(plans) == 1
    assert plans[0].image_index == 0
    assert plans[0].tools == ["denoise", "color_grading"]


@pytest.mark.asyncio
async def test_final_edit_planner_client_rejects_out_of_range_index() -> None:
    client = _planner_client()

    async def fake_request_plan(image_paths, context):
        return """
        [
          {
            "image_index": 2,
            "content": "매장 배경",
            "strategy": "밝기를 높인다.",
            "tools": ["color_grading"],
            "params": {
              "color_grading": {"temperature": "warm", "saturation": 0.1, "brightness": 0.1}
            }
          }
        ]
        """

    client._request_plan = fake_request_plan  # type: ignore[method-assign]

    with pytest.raises(FinalEditPlanningError, match="out-of-range"):
        await client.build_plans(
            ["a.jpg", "b.jpg"],
            FinalEditSessionContext(caption="배경 소개", keywords=["매장"]),
        )
