import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from redis.asyncio import Redis

from app.core.config import settings
from app.db.redis import get_redis
from app.schemas.sessions import (
    ExtractFramesRequest,
    ExtractFramesResponse,
    FinalEditRequest,
    FinalEditResponse,
    ProcessUtteranceRequest,
    ProcessUtteranceResponse,
)
from app.services.frame_extraction import (
    get_frame_extraction_service,
    process_extract_frames,
)
from app.services.final_edit import get_final_edit_service, process_final_edit
from app.services.keyword_extraction import (
    KeywordExtractionUnavailableError,
    get_keyword_extraction_service,
)
from app.services.sessions import process_utterance

router = APIRouter(prefix="/sessions", tags=["ai-sessions"])
logger = logging.getLogger(__name__)


@router.post(
    "/{session_id}/process-utterance",
    response_model=ProcessUtteranceResponse,
    response_model_exclude_none=True,
    summary="AI 기반 게시물 캡션 생성",
)
async def process_utterance_endpoint(
    session_id: str,
    payload: ProcessUtteranceRequest,
    request: Request,
    redis: Redis = Depends(get_redis),
) -> ProcessUtteranceResponse:
    keyword_service = get_keyword_extraction_service(request)
    logger.info(
        "process-utterance request received.",
        extra={
            "session_id": session_id,
            "payload_owner_persona": payload.owner_persona,
            "payload_weather_condition": payload.weather.condition,
            "utterance_length": len(payload.utterance),
        },
    )
    try:
        result = await process_utterance(
            session_id,
            payload,
            redis,
            keyword_service,
        )
    except KeywordExtractionUnavailableError as exc:
        cause = exc.__cause__
        logger.warning(
            "Keyword extraction failed during process-utterance: %s | cause=%r",
            exc,
            cause,
            extra={"session_id": session_id},
            exc_info=True,
        )
        raise HTTPException(
            status_code=503,
            detail="Keyword extraction is unavailable.",
        ) from exc
    logger.info(
        "process-utterance completed successfully.",
        extra={
            "session_id": session_id,
            "keyword_count": len(result.keywords),
        },
    )
    return ProcessUtteranceResponse(
        session_id=session_id,
        guide_text=result.guide_text,
        keywords=result.keywords if settings.DEBUG else None,
        caption=result.caption
    )


@router.post(
    "/{session_id}/extract-frames",
    response_model=ExtractFramesResponse,
    summary="가장 점수가 높은 프레임을 추출해 초안으로 업로드",
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


@router.post(
    "/{session_id}/final-edit",
    response_model=FinalEditResponse,
    summary="초안 이미지 방향을 보정하고 최종 이미지를 업로드",
)
async def final_edit_endpoint(
    session_id: str,
    payload: FinalEditRequest,
    request: Request,
    redis: Redis = Depends(get_redis),
) -> FinalEditResponse:
    if str(payload.session_id) != session_id:
        raise HTTPException(
            status_code=422,
            detail="Path session_id and body session_id must match.",
        )

    final_edit_service = get_final_edit_service(request)
    result = await process_final_edit(session_id, payload, redis, final_edit_service)
    return FinalEditResponse(
        session_id=session_id,
        status=result.status,
        results=result.results,
    )
