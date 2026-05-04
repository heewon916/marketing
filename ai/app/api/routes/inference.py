from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings

router = APIRouter(prefix="/inference", tags=["inference"])


class InferenceRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="User input for inference")
    model: str | None = Field(default=None, description="Optional model override")


class InferenceResponse(BaseModel):
    provider: str
    model: str
    prompt: str
    message: str


@router.post("", response_model=InferenceResponse, summary="추론 플레이스홀더")
def run_inference(payload: InferenceRequest) -> InferenceResponse:
    resolved_model = payload.model or settings.DEFAULT_MODEL
    return InferenceResponse(
        provider=settings.PROVIDER,
        model=resolved_model,
        prompt=payload.prompt,
        message="Inference pipeline scaffolded. Connect your model runtime here.",
    )
