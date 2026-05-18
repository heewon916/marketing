import pytest

from app.services.final_edit_planner import (
    TARGET_PROFILE_KIND_TONE,
    FinalEditPlannerClient,
    FinalEditPlanningError,
    FinalEditSessionContext,
    ImageEditPlan,
    build_upscale_only_plan,
    build_final_edit_prompt,
    load_final_edit_session_context,
    normalize_image_edit_plan,
    parse_image_edit_plans,
    resolve_owner_persona_target,
    resolve_owner_persona_preset,
)
from app.services.final_edit_tools import AESTHETIC_TARGET_TONE_PROFILE
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
            "owner_persona": "friendly",
            "caption": "포근한 디저트 소개",
            "draft_keyword:2": "따뜻한 분위기",
            "draft_keyword:1": "시그니처 케이크",
            "final_keyword:1": "1001:케이크",
        },
    )

    context = await load_final_edit_session_context(fake_redis_async, "sess-1")

    assert context.owner_persona == "friendly"
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

    assert context.owner_persona == "aesthetic"
    assert context.keywords == ["케이크", "테이블"]


def test_build_final_edit_prompt_includes_caption_and_keywords() -> None:
    prompt = build_final_edit_prompt(
        FinalEditSessionContext(
            owner_persona="friendly",
            caption="포근한 케이크 소개",
            keywords=["시그니처 케이크", "크림 디저트"],
        ),
        3,
    )

    assert "[owner_persona] friendly" in prompt
    assert "[target_preset_persona] friendly" in prompt
    assert "[caption] 포근한 케이크 소개" in prompt
    assert "[keywords] 시그니처 케이크, 크림 디저트" in prompt
    assert "\"contrast\"" in prompt
    assert "minimum adjustment needed" in prompt
    assert "color_grading" in prompt
    assert "Upscale must be included for every image" in prompt
    assert "it is 2x only" in prompt
    assert "exactly once as the last tool" in prompt
    assert "Denoise alone is not enough to justify upscale" in prompt
    assert "all 3 input images" in prompt
    assert "image_index from 0 to 2" in prompt


def test_build_final_edit_prompt_uses_aesthetic_tone_profile() -> None:
    prompt = build_final_edit_prompt(
        FinalEditSessionContext(
            owner_persona="aesthetic",
            caption="분위기 설명",
            keywords=["케이크"],
        ),
        1,
    )

    assert "[target_profile_kind] tone_profile" in prompt
    assert "\"brightness\"" in prompt
    assert "\"tolerance\"" in prompt
    assert "\"target\": 81.69" in prompt


def test_resolve_owner_persona_preset_falls_back_to_aesthetic() -> None:
    persona, preset, used_fallback = resolve_owner_persona_preset("unknown")

    assert persona == "aesthetic"
    assert used_fallback is True
    assert preset == AESTHETIC_TARGET_TONE_PROFILE


def test_resolve_owner_persona_target_marks_aesthetic_as_tone_profile() -> None:
    persona, target, used_fallback, target_kind = resolve_owner_persona_target(
        "aesthetic"
    )

    assert persona == "aesthetic"
    assert used_fallback is False
    assert target == AESTHETIC_TARGET_TONE_PROFILE
    assert target_kind == TARGET_PROFILE_KIND_TONE


def test_normalize_image_edit_plan_enforces_execution_order() -> None:
    normalized = normalize_image_edit_plan(
        ImageEditPlan(
            image_index=0,
            content="cake",
            strategy="upscale first",
            tools=["upscale", "sharpen", "denoise", "color_grading"],
            params={
                "upscale": {"scale": 4},
                "sharpen": {"strength": 0.3},
                "denoise": {"strength": 0.4},
                "color_grading": {"contrast": -10},
            },
        )
    )

    assert normalized.tools == ["denoise", "sharpen", "color_grading", "upscale"]
    assert normalized.params["upscale"] == {"scale": 2}


def test_normalize_image_edit_plan_appends_default_upscale() -> None:
    normalized = normalize_image_edit_plan(
        ImageEditPlan(
            image_index=0,
            content="cake",
            strategy="denoise and sharpen",
            tools=["sharpen", "denoise"],
            params={
                "sharpen": {"strength": 0.3},
                "denoise": {"strength": 0.4},
            },
        )
    )

    assert normalized.tools == ["denoise", "sharpen", "upscale"]
    assert normalized.params["upscale"] == {"scale": 2}


def test_normalize_image_edit_plan_deduplicates_upscale_to_single_last_step() -> None:
    normalized = normalize_image_edit_plan(
        ImageEditPlan(
            image_index=0,
            content="cake",
            strategy="duplicate upscale",
            tools=["upscale", "color_grading", "upscale", "denoise"],
            params={
                "upscale": {"scale": 4},
                "color_grading": {"contrast": -10},
                "denoise": {"strength": 0.4},
            },
        )
    )

    assert normalized.tools == ["denoise", "color_grading", "upscale"]
    assert normalized.tools.count("upscale") == 1
    assert normalized.params["upscale"] == {"scale": 2}


def test_build_upscale_only_plan_uses_default_two_x_scale() -> None:
    plan = build_upscale_only_plan(1)

    assert plan.image_index == 1
    assert plan.tools == ["color_grading", "upscale"]
    assert plan.params["color_grading"] == {}
    assert plan.params["upscale"] == {"scale": 2}


def test_build_upscale_only_plan_uses_persona_preset_for_non_aesthetic() -> None:
    plan = build_upscale_only_plan(1, owner_persona="friendly")

    assert plan.tools == ["color_grading", "upscale"]
    assert plan.params["color_grading"]["temperature"] == "warm"


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
        assert context.owner_persona == "friendly"
        assert context.caption == "포근한 디저트 소개"
        return """
        [
          {
            "image_index": 0,
            "content": "시그니처 케이크가 보인다.",
            "strategy": "현재 톤이 목표 프리셋보다 더 밝고 선명해서 색과 하이라이트를 살짝 낮춘다.",
            "tools": ["denoise", "color_grading"],
            "params": {
              "denoise": {"strength": 0.4},
              "color_grading": {
                "contrast": -8,
                "highlights": -10,
                "shadows": 6,
                "vibrance": -4,
                "saturation": -6,
                "temperature": "warm",
                "tone_curve_shadow_lift": 4
              }
            }
          }
        ]
        """

    client._request_plan = fake_request_plan  # type: ignore[method-assign]

    plans = await client.build_plans(
        ["a.jpg", "b.jpg"],
        FinalEditSessionContext(
            owner_persona="friendly",
            caption="포근한 디저트 소개",
            keywords=["케이크"],
        ),
    )

    assert len(plans) == 1
    assert plans[0].image_index == 0
    assert plans[0].tools == ["denoise", "color_grading", "upscale"]


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
