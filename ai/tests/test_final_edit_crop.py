import numpy as np
import pytest

from app.services.final_edit_tools import FinalEditToolRegistry, normalize_tool_params


def _portrait_image() -> np.ndarray:
    image = np.zeros((300, 180, 3), dtype=np.uint8)
    image[60:240, 40:140] = 180
    return image


def test_normalize_crop_params_filters_invalid_entries() -> None:
    normalized = normalize_tool_params(
        "crop",
        {
            "subject_boxes": [[10, 10, 60, 100], [1, 2, 1, 2], "bad"],
            "keep_edges": ["top", "top", "invalid"],
            "anchor_orientation": "portrait",
        },
    )

    assert normalized["subject_boxes"] == [[10, 10, 60, 100]]
    assert normalized["keep_edges"] == ["top"]
    assert normalized["anchor_orientation"] == "portrait"


def test_crop_tool_applies_portrait_three_by_four_crop() -> None:
    registry = FinalEditToolRegistry(upscale_enabled=False)
    cropped, metadata = registry.execute(
        "crop",
        _portrait_image(),
        {
            "subject_boxes": [[40, 80, 140, 220]],
            "keep_edges": [],
        },
    )

    assert metadata["crop_applied"] is True
    assert metadata["crop_reason"] == "applied"
    assert cropped.shape[1] / cropped.shape[0] == pytest.approx(3 / 4, rel=1e-2)


def test_crop_tool_honors_top_edge_pin() -> None:
    registry = FinalEditToolRegistry(upscale_enabled=False)
    cropped, metadata = registry.execute(
        "crop",
        _portrait_image(),
        {
            "subject_boxes": [[40, 0, 140, 120]],
            "keep_edges": ["top"],
        },
    )

    assert metadata["crop_applied"] is True
    assert metadata["crop_box"][1] == 0
    assert cropped.shape[1] / cropped.shape[0] == pytest.approx(3 / 4, rel=1e-2)


def test_crop_tool_skips_when_gain_is_too_small() -> None:
    registry = FinalEditToolRegistry(upscale_enabled=False)
    image = np.zeros((160, 160, 3), dtype=np.uint8)
    cropped, metadata = registry.execute(
        "crop",
        image,
        {
            "subject_boxes": [[10, 10, 150, 150]],
            "keep_edges": [],
        },
    )

    assert metadata["crop_applied"] is False
    assert metadata["crop_reason"] in {"gain_too_small", "gain_ratio_too_small"}
    assert cropped.shape == image.shape


def test_crop_tool_uses_anchor_orientation_for_carousel_consistency() -> None:
    registry = FinalEditToolRegistry(upscale_enabled=False)
    image = np.zeros((300, 180, 3), dtype=np.uint8)
    cropped, metadata = registry.execute(
        "crop",
        image,
        {
            "subject_boxes": [[40, 80, 140, 220]],
            "keep_edges": [],
            "anchor_orientation": "landscape",
        },
    )

    assert metadata["crop_applied"] is False
    assert metadata["crop_reason"] == "orientation_locked"
    assert cropped.shape == image.shape
