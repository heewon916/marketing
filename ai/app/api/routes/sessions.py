from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis

from app.core.config import settings
from app.db.redis import get_redis
from app.schemas.sessions import (
    ExtractFramesRequest,
    ExtractFramesResponse,
    ProcessUtteranceRequest,
    ProcessUtteranceResponse,
)
from app.services.frame_extraction import (
    get_frame_extraction_service,
    process_extract_frames,
)
from app.services.sessions import process_utterance

router = APIRouter(prefix="/sessions", tags=["ai-sessions"])


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


@router.post(
    "/{session_id}/extract-frames",
    response_model=ExtractFramesResponse,
    summary="Extract the highest-scoring frame and upload it as a draft",
)
async def extract_frames_endpoint(
    session_id: str,
    payload: ExtractFramesRequest,
    request: Request,
    redis: Redis = Depends(get_redis),
) -> ExtractFramesResponse:
    if str(payload.session_id) != session_id:
        raise HTTPException(
            status_code=422,
            detail="Path session_id and body session_id must match.",
        )

    frame_service = get_frame_extraction_service(request)
    result = await process_extract_frames(session_id, payload, redis, frame_service)
    return ExtractFramesResponse(
        session_id=session_id,
        status=result.status,
        drafts=result.drafts,
    )
