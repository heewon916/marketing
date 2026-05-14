from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from langgraph.graph import END, START, StateGraph

from app.services.final_edit_planner import ImageEditPlan
from app.services.final_edit_tools import FinalEditToolRegistry


@dataclass
class FinalEditImageState:
    image_path: Path
    plan: ImageEditPlan
    current_tool_index: int = 0
    output_path: Path | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class FinalEditAgent:
    """Scaffolding LangGraph agent for final-edit image execution."""

    def __init__(self, tool_registry: FinalEditToolRegistry) -> None:
        self.tool_registry = tool_registry
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(FinalEditImageState)
        graph.add_node("validate_plan", self._validate_plan)
        graph.add_node("finalize", self._finalize)
        graph.add_edge(START, "validate_plan")
        graph.add_edge("validate_plan", "finalize")
        graph.add_edge("finalize", END)
        return graph.compile()

    def _validate_plan(self, state: FinalEditImageState) -> FinalEditImageState:
        return state

    def _finalize(self, state: FinalEditImageState) -> FinalEditImageState:
        return state

    async def run(self, state: FinalEditImageState) -> FinalEditImageState:
        return await self.graph.ainvoke(state)
