import asyncio
from dataclasses import dataclass
import logging

from redis.asyncio import Redis

from app.core.config import settings
from app.logging import build_log_extra, preview_text
from app.schemas.sessions import ProcessUtteranceRequest
from app.services.caption_generation import (
    CaptionGenerationRequest,
    CaptionGenerationService,
    CaptionGenerationUnavailableError,
)
from app.services.content_purpose import ContentPurpose, MENU_PROMOTION_PURPOSE
from app.services.keyword_extraction import KeywordExtractionService
from app.services.menu_promotion_context import (
    MatchedMenuContext,
    MenuPromotionContextService,
)
from app.services.session_store import RedisSessionStore, session_key
from app.services.weather_tags import evaluate_weather_tags

STATUS_STARTED = "STARTED"
STATUS_TEXT_GENERATED = "TEXT_GENERATED"

HEALTH_CHECK_FALLBACK_SOURCE = "health_check_fallback"
HEALTH_CHECK_FAILURE_GUIDE_TEXT = (
    "사장님, 잠시 후 다시 시도해 주세요. "
    "지금은 가게의 분위기와 메뉴가 잘 보이도록 자유롭게 촬영해보세요."
)
HEALTH_CHECK_FAILURE_CAPTION = (
    "지금은 AI 캡션 생성에 필요한 내용이 충분하지 않아 잠시 후 다시 시도해 주세요."
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessUtteranceResult:
    status: str
    purpose: ContentPurpose
    weather_tags: list[str]
    draft_keywords: list[str]
    final_keywords: list[str]
    draft_caption: str
    guide_text: str
    caption: str


@dataclass
class TextGenerationOutcome:
    draft_caption: str
    guide_text: str
    stored_caption: str
    fallback_source: str | None


@dataclass
class CaptionPreparation:
    draft_keywords: list[str]
    final_keywords: list[str]
    caption_request: CaptionGenerationRequest


async def upsert_content_session(
    redis: Redis,
    session_id: str,
    scalar_fields: dict[str, str],
    draft_keywords: list[str] | None = None,
    final_keywords: list[str] | None = None,
    weather_tags: list[str] | None = None,
    drafts: list[str] | None = None,
    photos: list[str] | None = None,
    debug_fields: dict[str, str] | None = None,
) -> None:
    await RedisSessionStore(redis).upsert_content_session(
        session_id=session_id,
        scalar_fields=scalar_fields,
        draft_keywords=draft_keywords,
        final_keywords=final_keywords,
        weather_tags=weather_tags,
        drafts=drafts,
        photos=photos,
        debug_fields=debug_fields,
    )


def _session_store(redis: Redis) -> RedisSessionStore:
    return RedisSessionStore(redis)


async def _persist_process_utterance_started(
    store: RedisSessionStore,
    session_id: str,
    utterance: str,
    owner_persona: str,
    weather_tags: list[str],
) -> None:
    await store.upsert_content_session(
        session_id=session_id,
        scalar_fields={
            "caption": "",
            "owner_persona": owner_persona,
            "utterance": utterance,
        },
        weather_tags=weather_tags,
    )
    logger.info(
        "Stored initial process-utterance request fields in redis.",
        extra=build_log_extra(
            "session.process_utterance.redis_store_request.completed",
            component="session",
            stage="persist_redis",
            session_id=session_id,
            outcome="succeeded",
            utterance_length=len(utterance),
            weather_tag_count=len(weather_tags),
            initialized_field_count=2,
        ),
    )


def _build_keyword_state(
    extraction_result,
    session_id: str,
) -> list[str]:
    draft_keywords = list(extraction_result.draft_keywords)

    logger.info(
        "Keyword extraction finished.",
        extra=build_log_extra(
            "session.process_utterance.keyword_extraction.completed",
            component="session",
            stage="keyword_extraction",
            session_id=session_id,
            outcome="succeeded",
            purpose=MENU_PROMOTION_PURPOSE,
            draft_keyword_count=len(draft_keywords),
            draft_keywords_preview=", ".join(draft_keywords[:3]),
        ),
    )

    return draft_keywords


def _build_final_keyword_state(
    draft_keywords: list[str],
    session_id: str,
) -> list[str]:
    final_keywords = list(draft_keywords)
    logger.info(
        "Final keyword state fixed to draft keywords for menu promotion.",
        extra=build_log_extra(
            "session.process_utterance.final_keyword_state.completed",
            component="session",
            stage="final_keyword_state",
            session_id=session_id,
            outcome="succeeded",
            draft_keyword_count=len(draft_keywords),
            draft_keywords_preview=", ".join(draft_keywords[:3]),
            final_keyword_count=len(final_keywords),
            final_keywords_preview=", ".join(final_keywords[:3]),
        ),
    )
    return final_keywords


def _build_process_utterance_debug_fields(
    matched_menu_context: MatchedMenuContext | None = None,
) -> dict[str, str]:
    debug_fields = {
        "debug:purpose": MENU_PROMOTION_PURPOSE,
    }
    if matched_menu_context is not None:
        debug_fields["debug:menu_match_source"] = matched_menu_context.match_source
        debug_fields["debug:menu_candidate_count"] = (
            "1" if matched_menu_context.matched else "0"
        )
        if matched_menu_context.matched_keyword is not None:
            debug_fields["debug:matched_keyword"] = matched_menu_context.matched_keyword
        if matched_menu_context.menu_name is not None:
            debug_fields["debug:matched_menu_name"] = matched_menu_context.menu_name
    return debug_fields


async def _persist_process_utterance_result(
    store: RedisSessionStore,
    session_id: str,
    owner_persona: str,
    caption: str,
    weather_tags: list[str],
    draft_keywords: list[str],
    final_keywords: list[str],
    debug_fields: dict[str, str],
) -> None:
    await store.delete_fields(
        session_key(session_id),
        [
            "session_id",
            "store_id",
            "weather_condition",
            "weather_temperature",
            "date",
            "expires_at",
        ],
    )
    await store.upsert_content_session(
        session_id=session_id,
        scalar_fields={
            "status": STATUS_TEXT_GENERATED,
            "caption": caption,
            "owner_persona": owner_persona,
        },
        weather_tags=weather_tags,
        draft_keywords=draft_keywords,
        final_keywords=final_keywords,
        debug_fields=debug_fields,
    )
    logger.info(
        "Stored process-utterance result in redis.",
        extra=build_log_extra(
            "session.process_utterance.redis_store.completed",
            component="session",
            stage="persist_redis",
            session_id=session_id,
            outcome="succeeded",
            caption_length=len(caption),
        ),
    )


async def _build_health_check_fallback_result(
    store: RedisSessionStore,
    session_id: str,
    utterance: str,
    owner_persona: str,
    weather_tags: list[str],
    *,
    keyword_ok: bool,
    caption_ok: bool,
) -> ProcessUtteranceResult:
    logger.warning(
        "Pre-flight health check failed; returning fixed fallback caption.",
        extra=build_log_extra(
            "session.process_utterance.health_check.failed",
            component="session",
            stage="health_check",
            session_id=session_id,
            outcome="failed",
            keyword_server_healthy=keyword_ok,
            caption_server_healthy=caption_ok,
        ),
    )
    debug_fields = {
        "debug:purpose": MENU_PROMOTION_PURPOSE,
        "debug:text_generation_fallback_source": HEALTH_CHECK_FALLBACK_SOURCE,
        "debug:health_check_keyword_ok": "true" if keyword_ok else "false",
        "debug:health_check_caption_ok": "true" if caption_ok else "false",
    }
    await store.upsert_content_session(
        session_id=session_id,
        scalar_fields={
            "status": STATUS_TEXT_GENERATED,
            "caption": HEALTH_CHECK_FAILURE_CAPTION,
            "owner_persona": owner_persona,
            "utterance": utterance,
        },
        weather_tags=weather_tags,
        draft_keywords=[],
        final_keywords=[],
        debug_fields=debug_fields,
    )
    return ProcessUtteranceResult(
        status=STATUS_TEXT_GENERATED,
        purpose=MENU_PROMOTION_PURPOSE,
        weather_tags=weather_tags,
        draft_keywords=[],
        final_keywords=[],
        draft_caption=HEALTH_CHECK_FAILURE_CAPTION,
        guide_text=HEALTH_CHECK_FAILURE_GUIDE_TEXT,
        caption=HEALTH_CHECK_FAILURE_CAPTION,
    )


async def _run_preflight_health_checks(
    keyword_service: KeywordExtractionService,
    caption_service: CaptionGenerationService,
) -> tuple[bool, bool]:
    return await asyncio.gather(
        keyword_service.is_healthy(),
        caption_service.is_healthy(),
    )


def _log_keyword_extraction_start(
    session_id: str,
    payload: ProcessUtteranceRequest,
    weather_tags: list[str],
) -> None:
    logger.info(
        "Starting keyword extraction for process-utterance.",
        extra=build_log_extra(
            "session.process_utterance.keyword_extraction.started",
            component="session",
            stage="keyword_extraction",
            session_id=session_id,
            outcome="started",
            owner_persona=payload.owner_persona,
            weather_cloud_cover=payload.weather.cloud_cover,
            weather_tag_count=len(weather_tags),
            weather_tags_preview=", ".join(weather_tags[:3]),
            utterance_length=len(payload.utterance),
            utterance_preview=preview_text(
                payload.utterance,
                settings.LOG_EVENT_PREVIEW_MAX_LEN,
            )
            if settings.LOG_INCLUDE_RAW_IDENTIFIERS
            else None,
        ),
    )


async def _prepare_caption_request(
    session_id: str,
    payload: ProcessUtteranceRequest,
    weather_tags: list[str],
    keyword_service: KeywordExtractionService,
) -> CaptionPreparation:
    _log_keyword_extraction_start(session_id, payload, weather_tags)
    extraction_result = await keyword_service.extract_keywords(payload.utterance)
    draft_keywords = _build_keyword_state(
        extraction_result=extraction_result,
        session_id=session_id,
    )
    final_keywords = _build_final_keyword_state(
        draft_keywords=draft_keywords,
        session_id=session_id,
    )
    caption_request = CaptionGenerationRequest(
        draft_keywords=list(draft_keywords),
        owner_persona=payload.owner_persona,
        today=payload.date.isoformat(),
        utterance=payload.utterance,
        weather_tags=weather_tags,
    )
    return CaptionPreparation(
        draft_keywords=draft_keywords,
        final_keywords=final_keywords,
        caption_request=caption_request,
    )


async def _attach_matched_menu(
    session_id: str,
    payload: ProcessUtteranceRequest,
    caption_request: CaptionGenerationRequest,
    menu_promotion_context_service: MenuPromotionContextService,
) -> MatchedMenuContext:
    matched_menu_context = await menu_promotion_context_service.match_menu(
        store_id=payload.store_id,
        draft_keywords=caption_request.draft_keywords,
    )
    if matched_menu_context.matched:
        caption_request.menu_name = matched_menu_context.menu_name
        caption_request.menu_description = matched_menu_context.menu_description
        caption_request.matched_keyword = matched_menu_context.matched_keyword
    logger.info(
        "Matched menu retrieval completed.",
        extra=build_log_extra(
            "session.process_utterance.menu_match.completed",
            component="session",
            stage="menu_match",
            session_id=session_id,
            outcome="succeeded" if matched_menu_context.matched else "skipped",
            menu_match_source=matched_menu_context.match_source,
            matched_keyword=matched_menu_context.matched_keyword,
            matched_menu_name=matched_menu_context.menu_name,
        ),
    )
    return matched_menu_context


def _fallback_text_generation_outcome(
    caption_service: CaptionGenerationService,
    caption_request: CaptionGenerationRequest,
    fallback_source: str | None,
) -> TextGenerationOutcome:
    fallback_result = caption_service.build_fallback_result(
        caption_request,
        fallback_source=fallback_source,
    )
    return TextGenerationOutcome(
        draft_caption=fallback_result.result.draft_caption,
        guide_text=fallback_result.result.guide_text,
        stored_caption=fallback_result.result.stored_caption,
        fallback_source=fallback_result.fallback_source,
    )


async def _generate_text_outcome(
    session_id: str,
    weather_tags: list[str],
    caption_request: CaptionGenerationRequest,
    caption_service: CaptionGenerationService,
) -> TextGenerationOutcome:
    if not caption_request.draft_keywords:
        outcome = _fallback_text_generation_outcome(
            caption_service,
            caption_request,
            fallback_source=None,
        )
        logger.info(
            "Built text generation result from default guide fallback.",
            extra=build_log_extra(
                "session.process_utterance.text_generation.completed",
                component="session",
                stage="text_generation",
                session_id=session_id,
                outcome="fallback",
                text_generation_source="default_guide",
                purpose=MENU_PROMOTION_PURPOSE,
                weather_tag_count=len(weather_tags),
                weather_tags_preview=", ".join(weather_tags[:3]),
                draft_caption_length=len(outcome.draft_caption),
                guide_text_length=len(outcome.guide_text),
            ),
        )
        return outcome

    try:
        result = await caption_service.generate_text(caption_request)
        outcome = TextGenerationOutcome(
            draft_caption=result.draft_caption,
            guide_text=result.guide_text,
            stored_caption=result.stored_caption,
            fallback_source=None,
        )
        logger.info(
            "Built text generation result from caption model.",
            extra=build_log_extra(
                "session.process_utterance.text_generation.completed",
                component="session",
                stage="text_generation",
                session_id=session_id,
                outcome="succeeded",
                text_generation_source="caption_model",
                purpose=MENU_PROMOTION_PURPOSE,
                weather_tag_count=len(weather_tags),
                weather_tags_preview=", ".join(weather_tags[:3]),
                draft_caption_length=len(outcome.draft_caption),
                guide_text_length=len(outcome.guide_text),
            ),
        )
        return outcome
    except CaptionGenerationUnavailableError as exc:
        outcome = _fallback_text_generation_outcome(
            caption_service,
            caption_request,
            fallback_source="caption_model_fallback",
        )
        logger.warning(
            "Caption model generation failed; falling back to rule-based text generation: %s",
            exc,
            exc_info=True,
            extra=build_log_extra(
                "session.process_utterance.text_generation.completed",
                component="session",
                stage="text_generation",
                session_id=session_id,
                outcome="fallback",
                text_generation_source="rule_based_fallback",
                error_type=exc.__class__.__name__,
                purpose=MENU_PROMOTION_PURPOSE,
                weather_tag_count=len(weather_tags),
                weather_tags_preview=", ".join(weather_tags[:3]),
                draft_caption_length=len(outcome.draft_caption),
                guide_text_length=len(outcome.guide_text),
            ),
        )
        return outcome


async def process_utterance(
    session_id: str,
    payload: ProcessUtteranceRequest,
    redis: Redis,
    keyword_service: KeywordExtractionService,
    caption_service: CaptionGenerationService,
    menu_promotion_context_service: MenuPromotionContextService,
) -> ProcessUtteranceResult:
    store = _session_store(redis)
    weather_tags = evaluate_weather_tags(
        payload.weather,
        target_date=payload.date,
    )
    keyword_ok, caption_ok = await _run_preflight_health_checks(
        keyword_service,
        caption_service,
    )
    if not (keyword_ok and caption_ok):
        return await _build_health_check_fallback_result(
            store,
            session_id,
            payload.utterance,
            payload.owner_persona,
            weather_tags,
            keyword_ok=keyword_ok,
            caption_ok=caption_ok,
        )

    await _persist_process_utterance_started(
        store,
        session_id,
        payload.utterance,
        payload.owner_persona,
        weather_tags,
    )
    preparation = await _prepare_caption_request(
        session_id=session_id,
        payload=payload,
        weather_tags=weather_tags,
        keyword_service=keyword_service,
    )
    matched_menu_context = await _attach_matched_menu(
        session_id=session_id,
        payload=payload,
        caption_request=preparation.caption_request,
        menu_promotion_context_service=menu_promotion_context_service,
    )
    text_outcome = await _generate_text_outcome(
        session_id=session_id,
        weather_tags=weather_tags,
        caption_request=preparation.caption_request,
        caption_service=caption_service,
    )

    debug_fields = _build_process_utterance_debug_fields(
        matched_menu_context=matched_menu_context,
    )
    if text_outcome.fallback_source is not None:
        debug_fields["debug:text_generation_fallback_source"] = (
            text_outcome.fallback_source
        )
    await _persist_process_utterance_result(
        store=store,
        session_id=session_id,
        owner_persona=payload.owner_persona,
        caption=text_outcome.stored_caption,
        weather_tags=weather_tags,
        draft_keywords=preparation.draft_keywords,
        final_keywords=preparation.final_keywords,
        debug_fields=debug_fields,
    )

    return ProcessUtteranceResult(
        status=STATUS_TEXT_GENERATED,
        purpose=MENU_PROMOTION_PURPOSE,
        weather_tags=weather_tags,
        draft_keywords=preparation.draft_keywords,
        final_keywords=preparation.final_keywords,
        draft_caption=text_outcome.draft_caption,
        guide_text=text_outcome.guide_text,
        caption=text_outcome.stored_caption,
    )
