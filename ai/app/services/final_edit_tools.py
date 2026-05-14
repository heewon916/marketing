from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

import cv2
import numpy as np

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
        description="색온도, 채도, 밝기를 보정한다.",
        params_schema={
            "temperature": "warm 또는 cool",
            "saturation": "-1.0~1.0",
            "brightness": "-1.0~1.0",
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


def normalize_tool_params(tool_name: ToolName, params: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "upscale":
        scale = params.get("scale", 2)
        return {"scale": 4 if str(scale).strip() == "4" else 2}
    if tool_name == "denoise":
        return {"strength": _clamp_float(params.get("strength"), 0.5, 0.0, 1.0)}
    if tool_name == "color_grading":
        return {
            "temperature": _normalize_temperature(params.get("temperature", "warm")),
            "saturation": _clamp_float(params.get("saturation"), 0.0, -1.0, 1.0),
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
    scale = cast(int, params["scale"])
    height, width = image.shape[:2]
    return cv2.resize(
        image,
        (width * scale, height * scale),
        interpolation=cv2.INTER_LANCZOS4,
    )


def _tool_denoise(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    strength = cast(float, params["strength"])
    h_value = int(3 + strength * 12)
    return cv2.fastNlMeansDenoisingColored(image, None, h_value, h_value, 7, 21)


def _tool_color_grading(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    temperature = cast(str, params["temperature"])
    saturation = cast(float, params["saturation"])
    brightness = cast(float, params["brightness"])

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    if temperature == "warm":
        b_channel = cv2.add(b_channel, 15)
        a_channel = cv2.add(a_channel, 8)
    else:
        b_channel = cv2.subtract(b_channel, 15)
        a_channel = cv2.subtract(a_channel, 5)

    merged = cv2.merge([l_channel, a_channel, b_channel])
    result = cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)

    if saturation != 0.0:
        hsv = cv2.cvtColor(result, cv2.COLOR_BGR2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * (1 + saturation), 0, 255)
        result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    if brightness != 0.0:
        result = np.clip(result.astype(np.float32) * (1 + brightness), 0, 255).astype(
            np.uint8
        )

    return result


def _tool_sharpen(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    strength = cast(float, params["strength"])
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=3)
    return cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)


def _tool_background_blur(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
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
