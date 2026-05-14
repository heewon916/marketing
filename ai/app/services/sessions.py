import asyncio
from dataclasses import dataclass
import logging
from typing import Any

from redis.asyncio import Redis

from app.core.config import settings
from app.logging import build_log_extra, preview_text
from app.schemas.sessions import ProcessUtteranceRequest
from app.services.canonical_keyword_resolver import (
    CanonicalKeywordResolution,
    CanonicalKeywordResolverService,
)
from app.services.caption_generation import (
    CaptionGenerationRequest,
    CaptionGenerationService,
    CaptionGenerationUnavailableError,
)
from app.services.content_purpose import ContentPurpose
from app.services.keyword_extraction import KeywordExtractionService
from app.services.menu_promotion_context import (
    MenuPromotionContext,
    MenuPromotionContextService,
)
from app.services.reference_caption_retriever import (
    ReferenceCaptionRetrieverService,
    RetrievedReferenceCaption,
)
from app.services.session_store import RedisSessionStore, session_key
from app.services.weather_tags import evaluate_weather_tags

STATUS_STARTED = "STARTED"
STATUS_TEXT_GENERATED = "TEXT_GENERATED"
MENU_PROMOTION_PURPOSE = "\uba54\ub274 \ud64d\ubcf4"
DAILY_SHARE_PURPOSE = "\uc77c\uc0c1 \uacf5\uc720"
HEALTH_CHECK_FAILURE_GUIDE_TEXT = (
    "?ъ옣?? ?좎떆 ???ㅼ떆 ?쒕룄??二쇱꽭?? "
    "吏湲덉? 媛寃뚯쓽 遺꾩쐞湲곗? 硫붾돱媛 ??蹂댁씠?꾨줉 ?먯쑀濡?쾶 珥ъ쁺?대낫?몄슂."
)
HEALTH_CHECK_FAILURE_CAPTION = (
    "吏湲덉? AI 罹≪뀡 ?앹꽦???좎떆 ?댁슜?????놁뼱?? ?좎떆 ???ㅼ떆 ?쒕룄??二쇱꽭??"
)
HEALTH_CHECK_FALLBACK_SOURCE = "health_check_fallback"
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
    selected_menu_name: str | None


@dataclass
class CaptionPreparation:
    purpose: ContentPurpose
    draft_keywords: list[str]
    final_keywords: list[str]
    canonical_resolution: CanonicalKeywordResolution
    caption_request: CaptionGenerationRequest


def resolve_caption_keywords(
    draft_keywords: list[str],
    canonical_resolution: CanonicalKeywordResolution,
) -> list[str]:
    if not canonical_resolution.matches:
        return draft_keywords

    caption_keywords: list[str] = []
    for match in canonical_resolution.matches:
        if match.matched and match.display_name:
            caption_keywords.append(match.display_name)
        else:
            caption_keywords.append(match.draft_keyword)
    return caption_keywords or draft_keywords


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


def _build_reference_caption_log_details(
    references: list[RetrievedReferenceCaption],
) -> list[dict[str, Any]]:
    return [
        {
            "id": reference.caption_id,
            "score": (
                round(reference.score, 4) if reference.score is not None else None
            ),
            "content": reference.caption_content,
        }
        for reference in references
    ]


async def _persist_process_utterance_started(
    store: RedisSessionStore,
    session_id: str,
    utterance: str,
    weather_tags: list[str],
) -> None:
    await store.upsert_content_session(
        session_id=session_id,
        scalar_fields={
            "caption": "",
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
) -> tuple[ContentPurpose, list[str]]:
    purpose = extraction_result.purpose
    draft_keywords = list(extraction_result.draft_keywords)

    logger.info(
        "Keyword extraction finished.",
        extra=build_log_extra(
            "session.process_utterance.keyword_extraction.completed",
            component="session",
            stage="keyword_extraction",
            session_id=session_id,
            outcome="succeeded",
            purpose=purpose,
            draft_keyword_count=len(draft_keywords),
            draft_keywords_preview=", ".join(draft_keywords[:3]),
        ),
    )

    return purpose, draft_keywords


def _build_final_keyword_state(
    draft_keywords: list[str],
    resolution: CanonicalKeywordResolution,
    session_id: str,
) -> list[str]:
    final_keywords = list(resolution.final_keywords or draft_keywords)
    logger.info(
        "Canonical keyword resolution finished.",
        extra=build_log_extra(
            "session.process_utterance.canonical_resolution.completed",
            component="session",
            stage="canonical_resolution",
            session_id=session_id,
            outcome="succeeded",
            draft_keyword_count=len(draft_keywords),
            draft_keywords_preview=", ".join(draft_keywords[:3]),
            final_keyword_count=len(final_keywords),
            final_keywords_preview=", ".join(final_keywords[:3]),
            canonical_match_count=resolution.match_count,
            canonical_fallback_count=resolution.fallback_count,
        ),
    )
    return final_keywords


def _build_process_utterance_debug_fields(
    purpose: ContentPurpose,
    canonical_resolution: CanonicalKeywordResolution,
    menu_promotion_context: MenuPromotionContext | None = None,
    selected_menu_name: str | None = None,
) -> dict[str, str]:
    debug_fields = {
        "debug:purpose": purpose,
        "debug:canonical_match_count": str(canonical_resolution.match_count),
        "debug:canonical_fallback_count": str(canonical_resolution.fallback_count),
    }
    if menu_promotion_context is not None:
        debug_fields["debug:menu_candidate_source"] = menu_promotion_context.source
        debug_fields["debug:menu_candidate_count"] = str(
            len(menu_promotion_context.candidates)
        )
        debug_fields["debug:weather_matched_menu_count"] = str(
            menu_promotion_context.weather_matched_count
        )
    if selected_menu_name is not None:
        debug_fields["debug:selected_menu_name"] = selected_menu_name
    return debug_fields


async def _persist_process_utterance_result(
    store: RedisSessionStore,
    session_id: str,
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
            "owner_persona",
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
        "debug:text_generation_fallback_source": HEALTH_CHECK_FALLBACK_SOURCE,
        "debug:health_check_keyword_ok": "true" if keyword_ok else "false",
        "debug:health_check_caption_ok": "true" if caption_ok else "false",
    }
    await store.upsert_content_session(
        session_id=session_id,
        scalar_fields={
            "status": STATUS_TEXT_GENERATED,
            "caption": HEALTH_CHECK_FAILURE_CAPTION,
            "utterance": utterance,
        },
        weather_tags=weather_tags,
        draft_keywords=[],
        final_keywords=[],
        debug_fields=debug_fields,
    )
    return ProcessUtteranceResult(
        status=STATUS_TEXT_GENERATED,
        purpose=DAILY_SHARE_PURPOSE,
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
    canonical_keyword_resolver: CanonicalKeywordResolverService,
) -> CaptionPreparation:
    _log_keyword_extraction_start(session_id, payload, weather_tags)
    extraction_result = await keyword_service.extract_keywords(payload.utterance)
    purpose, draft_keywords = _build_keyword_state(
        extraction_result=extraction_result,
        session_id=session_id,
    )
    canonical_resolution = await canonical_keyword_resolver.resolve_keywords(
        draft_keywords
    )
    final_keywords = _build_final_keyword_state(
        draft_keywords=draft_keywords,
        resolution=canonical_resolution,
        session_id=session_id,
    )
    caption_request = CaptionGenerationRequest(
        purpose=purpose,
        keywords=resolve_caption_keywords(draft_keywords, canonical_resolution),
        owner_persona=payload.owner_persona,
        utterance=payload.utterance,
        weather_tags=weather_tags,
    )
    return CaptionPreparation(
        purpose=purpose,
        draft_keywords=draft_keywords,
        final_keywords=final_keywords,
        canonical_resolution=canonical_resolution,
        caption_request=caption_request,
    )


async def _attach_menu_candidates(
    session_id: str,
    payload: ProcessUtteranceRequest,
    weather_tags: list[str],
    purpose: ContentPurpose,
    caption_request: CaptionGenerationRequest,
    menu_promotion_context_service: MenuPromotionContextService,
) -> MenuPromotionContext | None:
    if purpose != MENU_PROMOTION_PURPOSE:
        return None

    menu_promotion_context = await menu_promotion_context_service.fetch_context(
        store_id=payload.store_id,
        weather_tags=weather_tags,
    )
    caption_request.menu_candidates = list(menu_promotion_context.candidates)
    logger.info(
        "Menu promotion context retrieval completed.",
        extra=build_log_extra(
            "session.process_utterance.menu_promotion_context.completed",
            component="session",
            stage="menu_promotion_context",
            session_id=session_id,
            outcome=(
                "succeeded" if menu_promotion_context.candidates else "skipped"
            ),
            menu_candidate_source=menu_promotion_context.source,
            menu_candidate_count=len(menu_promotion_context.candidates),
            weather_matched_menu_count=menu_promotion_context.weather_matched_count,
        ),
    )
    return menu_promotion_context


async def _attach_reference_captions(
    session_id: str,
    payload: ProcessUtteranceRequest,
    canonical_resolution: CanonicalKeywordResolution,
    caption_request: CaptionGenerationRequest,
    reference_caption_retriever: ReferenceCaptionRetrieverService,
) -> None:
    try:
        reference_caption_result = await reference_caption_retriever.retrieve(
            owner_persona=payload.owner_persona,
            utterance=payload.utterance,
            canonical_matches=canonical_resolution.matches,
        )
    except Exception as exc:
        logger.warning(
            "Reference caption retrieval failed; continuing without caption RAG.",
            exc_info=True,
            extra=build_log_extra(
                "session.process_utterance.reference_caption_retrieval.completed",
                component="session",
                stage="reference_caption_retrieval",
                session_id=session_id,
                outcome="failed",
                error_type=exc.__class__.__name__,
            ),
        )
        return

    if reference_caption_result.captions:
        caption_request.reference_captions = reference_caption_result.captions
    logger.info(
        "Reference caption retrieval completed.",
        extra=build_log_extra(
            "session.process_utterance.reference_caption_retrieval.completed",
            component="session",
            stage="reference_caption_retrieval",
            session_id=session_id,
            outcome=(
                "succeeded" if reference_caption_result.captions else "skipped"
            ),
            reference_caption_candidate_count=reference_caption_result.candidate_count,
            reference_caption_selected_count=len(reference_caption_result.captions),
            reference_caption_selected_ids=",".join(
                str(caption_id)
                for caption_id in reference_caption_result.selected_caption_ids
            )
            or None,
            reference_caption_selected_details=(
                _build_reference_caption_log_details(
                    reference_caption_result.references
                )
                if reference_caption_result.references
                else None
            ),
            reference_caption_fallback_reason=reference_caption_result.fallback_reason,
        ),
    )


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
        selected_menu_name=fallback_result.result.selected_menu_name,
    )


async def _generate_text_outcome(
    session_id: str,
    purpose: ContentPurpose,
    weather_tags: list[str],
    caption_request: CaptionGenerationRequest,
    caption_service: CaptionGenerationService,
) -> TextGenerationOutcome:
    if not caption_request.keywords:
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
                purpose=purpose,
                selected_menu_name=outcome.selected_menu_name,
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
            selected_menu_name=result.selected_menu_name,
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
                purpose=purpose,
                selected_menu_name=outcome.selected_menu_name,
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
                purpose=purpose,
                selected_menu_name=outcome.selected_menu_name,
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
    canonical_keyword_resolver: CanonicalKeywordResolverService,
    reference_caption_retriever: ReferenceCaptionRetrieverService,
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
            weather_tags,
            keyword_ok=keyword_ok,
            caption_ok=caption_ok,
        )

    await _persist_process_utterance_started(
        store,
        session_id,
        payload.utterance,
        weather_tags,
    )
    preparation = await _prepare_caption_request(
        session_id=session_id,
        payload=payload,
        weather_tags=weather_tags,
        keyword_service=keyword_service,
        canonical_keyword_resolver=canonical_keyword_resolver,
    )
    menu_promotion_context = await _attach_menu_candidates(
        session_id=session_id,
        payload=payload,
        weather_tags=weather_tags,
        purpose=preparation.purpose,
        caption_request=preparation.caption_request,
        menu_promotion_context_service=menu_promotion_context_service,
    )
    await _attach_reference_captions(
        session_id=session_id,
        payload=payload,
        canonical_resolution=preparation.canonical_resolution,
        caption_request=preparation.caption_request,
        reference_caption_retriever=reference_caption_retriever,
    )
    text_outcome = await _generate_text_outcome(
        session_id=session_id,
        purpose=preparation.purpose,
        weather_tags=weather_tags,
        caption_request=preparation.caption_request,
        caption_service=caption_service,
    )

    debug_fields = _build_process_utterance_debug_fields(
        purpose=preparation.purpose,
        canonical_resolution=preparation.canonical_resolution,
        menu_promotion_context=menu_promotion_context,
        selected_menu_name=text_outcome.selected_menu_name,
    )
    if text_outcome.fallback_source is not None:
        debug_fields["debug:text_generation_fallback_source"] = (
            text_outcome.fallback_source
        )
    await _persist_process_utterance_result(
        store=store,
        session_id=session_id,
        caption=text_outcome.stored_caption,
        weather_tags=weather_tags,
        draft_keywords=preparation.draft_keywords,
        final_keywords=preparation.final_keywords,
        debug_fields=debug_fields,
    )

    return ProcessUtteranceResult(
        status=STATUS_TEXT_GENERATED,
        purpose=preparation.purpose,
        weather_tags=weather_tags,
        draft_keywords=preparation.draft_keywords,
        final_keywords=preparation.final_keywords,
        draft_caption=text_outcome.draft_caption,
        guide_text=text_outcome.guide_text,
        caption=text_outcome.stored_caption,
    )
