from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

import numpy as np

from app.services.final_edit_runtime import import_cv2

ToolName = Literal[
    "upscale",
    "denoise",
    "color_grading",
    "sharpen",
    "background_blur",
]


@dataclass(frozen=True)
class FinalEditToolSpec:
    name: ToolName
    description: str
    params_schema: dict[str, Any]


SUPPORTED_TOOL_SPECS: tuple[FinalEditToolSpec, ...] = (
    FinalEditToolSpec(
        name="upscale",
        description="저해상도 이미지를 업스케일한다.",
        params_schema={"scale": "2 또는 4"},
    ),
    FinalEditToolSpec(
        name="denoise",
        description="이미지 노이즈를 줄인다.",
        params_schema={"strength": "0.0~1.0"},
    ),
    FinalEditToolSpec(
        name="color_grading",
        description="목표 톤에 맞춰 색온도와 톤 밸런스를 미세 조정한다.",
        params_schema={
            "contrast": "-100~100",
            "highlights": "-100~100",
            "shadows": "-100~100",
            "vibrance": "-100~100",
            "saturation": "-100~100",
            "temperature": "warm 또는 cool",
            "tone_curve_shadow_lift": "-100~100",
            "brightness": "-1.0~1.0 (legacy)",
        },
    ),
    FinalEditToolSpec(
        name="sharpen",
        description="샤프닝으로 디테일을 살린다.",
        params_schema={"strength": "0.0~1.0"},
    ),
    FinalEditToolSpec(
        name="background_blur",
        description="배경을 흐리게 만든다.",
        params_schema={"blur_radius": "1~20"},
    ),
)


def supported_tool_names() -> tuple[ToolName, ...]:
    return tuple(spec.name for spec in SUPPORTED_TOOL_SPECS)


def _clamp_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return default
    return max(minimum, min(maximum, numeric))


def _normalize_temperature(value: Any) -> str:
    normalized = str(value).strip().lower()
    if normalized in {"warm", "cool"}:
        return normalized
    return "warm"


def _clamp_percent(value: Any, default: float = 0.0) -> float:
    return _clamp_float(value, default, -100.0, 100.0)


def _is_legacy_color_grading_params(params: dict[str, Any]) -> bool:
    known_legacy_keys = {"temperature", "saturation", "brightness"}
    known_new_keys = {
        "contrast",
        "highlights",
        "shadows",
        "vibrance",
        "tone_curve_shadow_lift",
    }
    if any(key in params for key in known_new_keys):
        return False
    if not set(params).issubset(known_legacy_keys):
        return False
    try:
        saturation = float(params.get("saturation", 0.0))
    except (TypeError, ValueError):
        return True
    return abs(saturation) <= 1.0 or "brightness" in params


def normalize_tool_params(tool_name: ToolName, params: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "upscale":
        scale = params.get("scale", 2)
        return {"scale": 4 if str(scale).strip() == "4" else 2}
    if tool_name == "denoise":
        return {"strength": _clamp_float(params.get("strength"), 0.5, 0.0, 1.0)}
    if tool_name == "color_grading":
        legacy_mode = _is_legacy_color_grading_params(params)
        normalized_saturation = (
            _clamp_float(params.get("saturation"), 0.0, -1.0, 1.0) * 100.0
            if legacy_mode
            else _clamp_percent(params.get("saturation"), 0.0)
        )
        return {
            "contrast": _clamp_percent(params.get("contrast"), 0.0),
            "highlights": _clamp_percent(params.get("highlights"), 0.0),
            "shadows": _clamp_percent(params.get("shadows"), 0.0),
            "vibrance": _clamp_percent(params.get("vibrance"), 0.0),
            "temperature": _normalize_temperature(params.get("temperature", "warm")),
            "saturation": normalized_saturation,
            "tone_curve_shadow_lift": _clamp_percent(
                params.get("tone_curve_shadow_lift"),
                0.0,
            ),
            "brightness": _clamp_float(params.get("brightness"), 0.0, -1.0, 1.0),
        }
    if tool_name == "sharpen":
        return {"strength": _clamp_float(params.get("strength"), 0.5, 0.0, 1.0)}
    if tool_name == "background_blur":
        blur_radius = params.get("blur_radius", 5)
        try:
            blur_radius_int = int(blur_radius)
        except (TypeError, ValueError):
            blur_radius_int = 5
        return {"blur_radius": max(1, min(20, blur_radius_int))}
    raise ValueError(f"Unsupported tool: {tool_name}")


def _tool_upscale(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    cv2 = import_cv2()
    scale = cast(int, params["scale"])
    height, width = image.shape[:2]
    return cv2.resize(
        image,
        (width * scale, height * scale),
        interpolation=cv2.INTER_LANCZOS4,
    )


def _tool_denoise(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    cv2 = import_cv2()
    strength = cast(float, params["strength"])
    h_value = int(3 + strength * 12)
    return cv2.fastNlMeansDenoisingColored(image, None, h_value, h_value, 7, 21)


def _tool_color_grading(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    cv2 = import_cv2()
    contrast = cast(float, params["contrast"])
    highlights = cast(float, params["highlights"])
    shadows = cast(float, params["shadows"])
    vibrance = cast(float, params["vibrance"])
    temperature = cast(str, params["temperature"])
    saturation = cast(float, params["saturation"])
    tone_curve_shadow_lift = cast(float, params["tone_curve_shadow_lift"])
    brightness = cast(float, params["brightness"])

    result = image.astype(np.float32)
    if temperature == "warm":
        result[:, :, 2] += 8.0
        result[:, :, 1] += 2.0
        result[:, :, 0] -= 6.0
    else:
        result[:, :, 0] += 8.0
        result[:, :, 2] -= 6.0

    if contrast != 0.0:
        contrast_factor = 1.0 + (contrast / 100.0) * 0.7
        result = (result - 127.5) * contrast_factor + 127.5

    if brightness != 0.0:
        result = result * (1.0 + brightness)

    luminance = (
        0.114 * result[:, :, 0] + 0.587 * result[:, :, 1] + 0.299 * result[:, :, 2]
    )
    normalized_luminance = np.clip(luminance / 255.0, 0.0, 1.0)
    highlight_mask = normalized_luminance**2
    shadow_mask = (1.0 - normalized_luminance) ** 2

    if highlights != 0.0:
        result += highlight_mask[:, :, None] * (highlights * 0.8)

    if shadows != 0.0:
        result += shadow_mask[:, :, None] * (shadows * 0.8)

    if tone_curve_shadow_lift != 0.0:
        result += shadow_mask[:, :, None] * (tone_curve_shadow_lift * 0.7)

    if vibrance != 0.0 or saturation != 0.0:
        hsv = cv2.cvtColor(
            np.clip(result, 0, 255).astype(np.uint8),
            cv2.COLOR_BGR2HSV,
        ).astype(np.float32)
        saturation_channel = hsv[:, :, 1]
        if vibrance != 0.0:
            low_saturation_mask = 1.0 - (saturation_channel / 255.0)
            saturation_channel += low_saturation_mask * (vibrance * 1.1)
        if saturation != 0.0:
            saturation_channel *= 1.0 + (saturation / 100.0)
        hsv[:, :, 1] = np.clip(saturation_channel, 0, 255)
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(
            np.float32
        )

    return np.clip(result, 0, 255).astype(np.uint8)


def _tool_sharpen(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    cv2 = import_cv2()
    strength = cast(float, params["strength"])
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=3)
    return cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)


def _tool_background_blur(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    cv2 = import_cv2()
    blur_radius = cast(int, params["blur_radius"])
    kernel = blur_radius * 2 + 1
    blurred = cv2.GaussianBlur(image, (kernel, kernel), 0)

    height, width = image.shape[:2]
    y1, y2 = height // 4, height * 3 // 4
    x1, x2 = width // 4, width * 3 // 4
    blurred[y1:y2, x1:x2] = image[y1:y2, x1:x2]
    return blurred


class FinalEditToolRegistry:
    """Registry for final-edit tool execution."""

    def __init__(self) -> None:
        self._tool_names = supported_tool_names()
        self._tool_functions = {
            "upscale": _tool_upscale,
            "denoise": _tool_denoise,
            "color_grading": _tool_color_grading,
            "sharpen": _tool_sharpen,
            "background_blur": _tool_background_blur,
        }

    @property
    def tool_names(self) -> tuple[ToolName, ...]:
        return self._tool_names

    def execute(
        self,
        tool_name: ToolName,
        image: np.ndarray,
        params: dict[str, Any],
    ) -> np.ndarray:
        normalized_params = normalize_tool_params(tool_name, params)
        return self._tool_functions[tool_name](image, normalized_params)
