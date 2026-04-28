from fastapi import APIRouter, Depends
from redis.asyncio import Redis

from app.core.config import settings
from app.db.redis import get_redis
from app.schemas.sessions import ProcessUtteranceRequest, ProcessUtteranceResponse
from app.services.sessions import process_utterance

router = APIRouter(prefix="/ai/sessions", tags=["ai-sessions"])


@router.post(
    "/{session_id}/process-utterance",
    response_model=ProcessUtteranceResponse,
    response_model_exclude_none=True,
    summary="AI 기반 게시물 캡션 생성",
)
async def process_utterance_endpoint(
    session_id: str,
    payload: ProcessUtteranceRequest,
    redis: Redis = Depends(get_redis),
) -> ProcessUtteranceResponse:
    result = await process_utterance(session_id, payload, redis)
    return ProcessUtteranceResponse(
        session_id=session_id,
        guide_text=result.guide_text,
        keywords=result.keywords if settings.DEBUG else None,
    )
