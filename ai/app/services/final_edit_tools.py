from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

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


class FinalEditToolRegistry:
    """Scaffolding registry for final-edit tool execution."""

    def __init__(self) -> None:
        self._tool_names = supported_tool_names()

    @property
    def tool_names(self) -> tuple[ToolName, ...]:
        return self._tool_names

    def execute(
        self,
        tool_name: ToolName,
        image: np.ndarray,
        params: dict[str, Any],
    ) -> np.ndarray:
        raise NotImplementedError("Tool execution is implemented in a later milestone.")
