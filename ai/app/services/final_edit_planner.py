from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from fastapi import Request

from app.core.config import LlamaModelClientSettings, settings
from app.services.final_edit_tools import ToolName


@dataclass(frozen=True)
class FinalEditSessionContext:
    caption: str
    keywords: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ImageEditPlan:
    image_index: int
    content: str
    strategy: str
    tools: list[ToolName]
    params: dict[str, dict[str, Any]]


class FinalEditPlannerClient:
    """Scaffolding client for the VLM planner request."""

    def __init__(
        self,
        model_settings: LlamaModelClientSettings,
        model_name: str,
    ) -> None:
        self.model_settings = model_settings
        self.model_name = model_name

    async def preload(self) -> None:
        return None

    async def build_plans(
        self,
        image_paths: list[str],
        context: FinalEditSessionContext,
    ) -> list[ImageEditPlan]:
        raise NotImplementedError("Planner execution is implemented in a later milestone.")


def build_final_edit_planner_client() -> FinalEditPlannerClient:
    return FinalEditPlannerClient(
        model_settings=settings.final_edit_model_client,
        model_name=settings.FINAL_EDIT_MODEL_NAME,
    )


def get_final_edit_planner_client(request: Request) -> FinalEditPlannerClient:
    service = getattr(request.app.state, "final_edit_planner_client", None)
    if service is None:
        raise RuntimeError("Final edit planner client is not initialized.")
    return service
