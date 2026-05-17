from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, cast

import numpy as np

from app.services.final_edit_runtime import import_cv2
from app.services.final_edit_upscaler import get_realesrgan_upscaler

ToolName = Literal[
    "upscale",
    "denoise",
    "color_grading",
    "sharpen",
    "background_blur",
]

AESTHETIC_TARGET_TONE_PROFILE: dict[str, dict[str, float]] = {
    "brightness": {"target": 81.69, "tolerance": 40.71},
    "contrast": {"target": 47.52, "tolerance": 13.68},
    "black_point": {"target": 18.88, "tolerance": 21.76},
    "white_point": {"target": 163.12, "tolerance": 44.14},
    "temperature": {"target": 13.58, "tolerance": 11.81},
    "tint": {"target": 5.23, "tolerance": 6.26},
    "saturation": {"target": 106.89, "tolerance": 32.23},
}
AESTHETIC_TONE_METRIC_KEYS: tuple[str, ...] = (
    "brightness",
    "contrast",
    "black_point",
    "white_point",
    "temperature",
    "tint",
    "saturation",
)
_TRIMMED_BRIGHTNESS_LOWER_PERCENTILE = 10.0
_TRIMMED_BRIGHTNESS_UPPER_PERCENTILE = 90.0
_HIGHLIGHT_PIXEL_THRESHOLD = 235.0
_HIGHLIGHT_RATIO_LOW = 0.03
_HIGHLIGHT_RATIO_MEDIUM = 0.08


@dataclass(frozen=True)
class FinalEditToolSpec:
    name: ToolName
    description: str
    params_schema: dict[str, Any]


SUPPORTED_TOOL_SPECS: tuple[FinalEditToolSpec, ...] = (
    FinalEditToolSpec(
        name="upscale",
        description="이미지를 업스케일한다.",
        params_schema={"scale": "2 only"},
    ),
    FinalEditToolSpec(
        name="denoise",
        description="이미지 노이즈를 줄인다.",
        params_schema={"strength": "0.0~1.0"},
    ),
    FinalEditToolSpec(
        name="color_grading",
        description="목표 톤에 맞춰 색온도와 채도, 명암을 미세 조정한다.",
        params_schema={
            "contrast": "-100~100",
            "highlights": "-100~100",
            "shadows": "-100~100",
            "vibrance": "-100~100",
            "saturation": "-100~100",
            "temperature": "warm 또는 cool",
            "temperature_strength": "0.0~1.0 (internal)",
            "tint": "-100~100 (internal)",
            "tint_strength": "0.0~1.0 (internal)",
            "tone_curve_shadow_lift": "-100~100",
            "brightness": "-1.0~1.0 (legacy)",
        },
    ),
    FinalEditToolSpec(
        name="sharpen",
        description="샤프로 디테일을 올린다.",
        params_schema={"strength": "0.0~1.0"},
    ),
    FinalEditToolSpec(
        name="background_blur",
        description="배경을 부드럽게 흐린다.",
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
        "temperature_strength",
        "tint",
        "tint_strength",
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


def _empty_color_grading_params() -> dict[str, Any]:
    return {
        "contrast": 0.0,
        "highlights": 0.0,
        "shadows": 0.0,
        "vibrance": 0.0,
        "temperature": "warm",
        "temperature_strength": 0.0,
        "tint": 0.0,
        "tint_strength": 0.0,
        "saturation": 0.0,
        "tone_curve_shadow_lift": 0.0,
        "brightness": 0.0,
    }


def _is_gap_within_skip_threshold(gap: float, tolerance: float) -> bool:
    return abs(gap) <= tolerance * 0.5


def _scale_gap_to_percent(gap: float, tolerance: float, multiplier: float) -> float:
    safe_tolerance = max(tolerance, 1.0)
    return _clamp_percent((gap / safe_tolerance) * multiplier)


def _scale_gap_to_unit_interval(
    gap: float,
    tolerance: float,
    multiplier: float,
) -> float:
    safe_tolerance = max(tolerance, 1.0)
    return _clamp_float((gap / safe_tolerance) * multiplier, 0.0, -1.0, 1.0)


def _trimmed_mean(
    values: np.ndarray,
    lower_percentile: float,
    upper_percentile: float,
) -> float:
    flattened = values.reshape(-1).astype(np.float64)
    lower_bound = float(np.percentile(flattened, lower_percentile))
    upper_bound = float(np.percentile(flattened, upper_percentile))
    trimmed = flattened[
        (flattened >= lower_bound) & (flattened <= upper_bound)
    ]
    if trimmed.size == 0:
        return float(np.mean(flattened))
    return float(np.mean(trimmed))


def _attenuate_negative_highlights(
    highlight_adjustment: float,
    highlight_area_ratio: float,
) -> float:
    if highlight_adjustment >= 0.0:
        return highlight_adjustment
    if highlight_area_ratio < _HIGHLIGHT_RATIO_LOW:
        return round(highlight_adjustment * 0.25, 2)
    if highlight_area_ratio < _HIGHLIGHT_RATIO_MEDIUM:
        return round(highlight_adjustment * 0.5, 2)
    return highlight_adjustment


def _attenuate_combined_global_darkening(
    brightness_adjustment: float,
    highlight_adjustment: float,
    highlight_area_ratio: float,
) -> float:
    if (
        brightness_adjustment < 0.0
        and highlight_adjustment < 0.0
        and highlight_area_ratio < _HIGHLIGHT_RATIO_MEDIUM
    ):
        return round(brightness_adjustment * 0.7, 4)
    return brightness_adjustment


def normalize_tool_params(tool_name: ToolName, params: dict[str, Any]) -> dict[str, Any]:
    if tool_name == "upscale":
        return {"scale": 2}
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
            "temperature_strength": _clamp_float(
                params.get("temperature_strength"),
                1.0 if "temperature" in params else 0.0,
                0.0,
                1.0,
            ),
            "tint": _clamp_percent(params.get("tint"), 0.0),
            "tint_strength": _clamp_float(
                params.get("tint_strength"),
                1.0 if "tint" in params else 0.0,
                0.0,
                1.0,
            ),
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
    return get_realesrgan_upscaler().upscale(image, 2)


def _tool_denoise(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    cv2 = import_cv2()
    strength = cast(float, params["strength"])
    h_value = int(3 + strength * 12)
    return cv2.fastNlMeansDenoisingColored(image, None, h_value, h_value, 7, 21)


def analyze_image_tone(image: np.ndarray) -> dict[str, float]:
    cv2 = import_cv2()
    working = image
    height, width = working.shape[:2]
    if max(height, width) > 1024:
        scale = 1024.0 / float(max(height, width))
        working = cv2.resize(working, (int(width * scale), int(height * scale)))

    lab = cv2.cvtColor(working, cv2.COLOR_BGR2LAB)
    l_channel = lab[:, :, 0].astype(np.float64)
    a_channel = lab[:, :, 1].astype(np.float64) - 128.0
    b_channel = lab[:, :, 2].astype(np.float64) - 128.0

    hsv = cv2.cvtColor(working, cv2.COLOR_BGR2HSV)
    saturation_channel = hsv[:, :, 1].astype(np.float64)
    brightness = _trimmed_mean(
        l_channel,
        _TRIMMED_BRIGHTNESS_LOWER_PERCENTILE,
        _TRIMMED_BRIGHTNESS_UPPER_PERCENTILE,
    )
    highlight_area_ratio = float(
        np.mean(l_channel >= _HIGHLIGHT_PIXEL_THRESHOLD)
    )

    return {
        "brightness": round(brightness, 2),
        "contrast": round(float(np.std(l_channel)), 2),
        "black_point": round(float(np.percentile(l_channel, 5)), 2),
        "white_point": round(float(np.percentile(l_channel, 95)), 2),
        "temperature": round(float(np.mean(b_channel)), 2),
        "tint": round(float(np.mean(a_channel)), 2),
        "saturation": round(float(np.mean(saturation_channel)), 2),
        "highlight_area_ratio": round(highlight_area_ratio, 4),
    }


def build_aesthetic_color_grading_params(
    image: np.ndarray,
) -> tuple[dict[str, Any], dict[str, Any]]:
    current_tone = analyze_image_tone(image)
    applied_params = _empty_color_grading_params()
    gap_by_metric: dict[str, float] = {}
    skip_by_metric: dict[str, bool] = {}
    threshold_by_metric: dict[str, float] = {}

    for metric_name in AESTHETIC_TONE_METRIC_KEYS:
        target_config = AESTHETIC_TARGET_TONE_PROFILE[metric_name]
        target = float(target_config["target"])
        tolerance = float(target_config["tolerance"])
        gap = round(target - current_tone[metric_name], 2)
        should_skip = _is_gap_within_skip_threshold(gap, tolerance)

        gap_by_metric[metric_name] = gap
        skip_by_metric[metric_name] = should_skip
        threshold_by_metric[metric_name] = round(tolerance * 0.5, 2)

        if should_skip:
            continue

        if metric_name == "brightness":
            applied_params["brightness"] = _scale_gap_to_unit_interval(
                gap,
                tolerance,
                0.35,
            )
        elif metric_name == "contrast":
            applied_params["contrast"] = _scale_gap_to_percent(gap, tolerance, 40.0)
        elif metric_name == "black_point":
            applied_params["tone_curve_shadow_lift"] = _scale_gap_to_percent(
                gap,
                tolerance,
                40.0,
            )
        elif metric_name == "white_point":
            applied_params["highlights"] = _attenuate_negative_highlights(
                _scale_gap_to_percent(gap, tolerance, 45.0),
                current_tone.get("highlight_area_ratio", 0.0),
            )
        elif metric_name == "temperature":
            applied_params["temperature"] = "warm" if gap >= 0.0 else "cool"
            applied_params["temperature_strength"] = _clamp_float(
                abs(gap) / max(tolerance, 1.0),
                0.0,
                0.0,
                1.0,
            )
        elif metric_name == "tint":
            applied_params["tint"] = _scale_gap_to_percent(gap, tolerance, 45.0)
            applied_params["tint_strength"] = _clamp_float(
                abs(gap) / max(tolerance, 1.0),
                0.0,
                0.0,
                1.0,
            )
        elif metric_name == "saturation":
            applied_params["saturation"] = _scale_gap_to_percent(gap, tolerance, 35.0)

    applied_params["brightness"] = _attenuate_combined_global_darkening(
        cast(float, applied_params["brightness"]),
        cast(float, applied_params["highlights"]),
        current_tone.get("highlight_area_ratio", 0.0),
    )

    normalized_params = normalize_tool_params("color_grading", applied_params)
    debug_payload = {
        "current_tone": current_tone,
        "target_tone": AESTHETIC_TARGET_TONE_PROFILE,
        "gap_by_metric": gap_by_metric,
        "skip_by_metric": skip_by_metric,
        "skip_threshold_by_metric": threshold_by_metric,
        "applied_params": normalized_params,
    }
    return normalized_params, debug_payload


def _tool_color_grading(image: np.ndarray, params: dict[str, Any]) -> np.ndarray:
    cv2 = import_cv2()
    contrast = cast(float, params["contrast"])
    highlights = cast(float, params["highlights"])
    shadows = cast(float, params["shadows"])
    vibrance = cast(float, params["vibrance"])
    temperature = cast(str, params["temperature"])
    temperature_strength = cast(float, params["temperature_strength"])
    tint = cast(float, params["tint"])
    tint_strength = cast(float, params["tint_strength"])
    saturation = cast(float, params["saturation"])
    tone_curve_shadow_lift = cast(float, params["tone_curve_shadow_lift"])
    brightness = cast(float, params["brightness"])

    result = image.astype(np.float32)
    if temperature_strength > 0.0:
        if temperature == "warm":
            result[:, :, 2] += 8.0 * temperature_strength
            result[:, :, 1] += 2.0 * temperature_strength
            result[:, :, 0] -= 6.0 * temperature_strength
        else:
            result[:, :, 0] += 8.0 * temperature_strength
            result[:, :, 2] -= 6.0 * temperature_strength

    if tint != 0.0 and tint_strength > 0.0:
        tint_shift = (tint / 100.0) * 24.0 * tint_strength
        result[:, :, 2] += tint_shift * 0.65
        result[:, :, 0] += tint_shift * 0.35
        result[:, :, 1] -= tint_shift

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
