from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import json
import logging
from pathlib import Path
import shutil
from tempfile import mkdtemp
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute

from app.api.main import api_router
from app.core.config import settings
from app.db.postgres import dispose_engine
from app.db.redis import close_redis, get_redis_client
from app.logging import (
    build_log_extra,
    configure_app_logging,
    new_request_id,
    preview_text,
    reset_request_id,
    set_request_id,
)
from app.perfectframe.dependencies import get_dependencies
from app.perfectframe.extractors import BestFrameExtractor
from app.perfectframe.schemas import ExtractorConfig
from app.services.frame_extraction import (
    FrameExtractionService,
    S3DraftUploader,
    S3VideoDownloader,
)
from app.services.final_edit import (
    FinalEditService,
    S3DraftImageDownloader,
    S3FinalImageUploader,
)
from app.services.caption_generation import (
    CaptionGenerationUnavailableError,
    build_caption_generation_service,
)
from app.services.keyword_extraction import (
    KeywordExtractionUnavailableError,
    build_keyword_extraction_service,
)
from app.services.canonical_keyword_resolver import (
    build_canonical_keyword_resolver_service,
)
from app.services.reference_caption_retriever import (
    build_reference_caption_retriever_service,
)
from app.services.menu_promotion_context import (
    build_menu_promotion_context_service,
)

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"


def _request_payload_summary(request: Request, payload: dict[str, object]) -> dict[str, object]:
    summary: dict[str, object] = {}
    store_id = payload.get("store_id")
    if store_id is not None and settings.LOG_INCLUDE_RAW_IDENTIFIERS:
        summary["store_id"] = str(store_id)

    utterance = payload.get("utterance")
    if isinstance(utterance, str):
        summary["utterance_length"] = len(utterance)
        if settings.LOG_INCLUDE_RAW_IDENTIFIERS:
            summary["utterance_preview"] = preview_text(
                utterance,
                settings.LOG_EVENT_PREVIEW_MAX_LEN,
            )

    video_key = payload.get("video")
    if isinstance(video_key, str):
        summary["video_present"] = True
        if settings.LOG_INCLUDE_RAW_IDENTIFIERS:
            summary["video_key"] = video_key

    drafts = payload.get("drafts")
    if isinstance(drafts, list):
        summary["draft_count"] = len(drafts)
        if settings.LOG_INCLUDE_RAW_IDENTIFIERS:
            summary["draft_keys"] = drafts[:3]

    client = request.client
    if client is not None:
        summary["client_host"] = client.host

    return summary


async def _read_request_payload(request: Request) -> tuple[bytes, dict[str, object] | None]:
    if request.method not in {"POST", "PUT", "PATCH"}:
        return b"", None

    body = await request.body()

    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = receive  # type: ignore[attr-defined]

    if not body:
        return body, None
    if "application/json" not in request.headers.get("content-type", ""):
        return body, None

    try:
        parsed = json.loads(body)
    except json.JSONDecodeError:
        return body, None

    if isinstance(parsed, dict):
        return body, parsed
    return body, None


def _route_label(request: Request) -> str:
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path)


def _session_id_from_path(request: Request) -> str | None:
    value = request.path_params.get("session_id")
    if value is None:
        return None
    return str(value)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    caption_client = settings.caption_model_client
    keyword_client = settings.keyword_model_client
    redis = get_redis_client()
    temp_root = Path(mkdtemp(prefix="ai-frame-extractor-"))
    logger.info(
        "AI service startup initialized temporary workspace.",
        extra=build_log_extra(
            "app.startup.temp_root_created",
            component="startup",
            outcome="started",
            temp_root=str(temp_root),
        ),
    )
    extractor_config = ExtractorConfig(
        input_directory=temp_root,
        output_directory=temp_root,
    )
    dependencies = get_dependencies(extractor_config)
    extractor = BestFrameExtractor(
        dependencies.config,
        dependencies.image_processor,
        dependencies.video_processor,
        dependencies.evaluator,
    )

    app.state.frame_extractor_config = extractor_config
    app.state.best_frame_extractor = extractor
    app.state.frame_extraction_temp_root = temp_root
    app.state.frame_extraction_service = FrameExtractionService(
        extractor_config=extractor_config,
        extractor=extractor,
        downloader=S3VideoDownloader(),
        uploader=S3DraftUploader(),
        temp_root=temp_root,
    )

    app.state.final_edit_service = FinalEditService(
        downloader=S3DraftImageDownloader(),
        uploader=S3FinalImageUploader(),
        temp_root=temp_root / "final-edit",
    )
    app.state.keyword_extraction_service = build_keyword_extraction_service()
    app.state.caption_generation_service = build_caption_generation_service()
    app.state.canonical_keyword_resolver_service = (
        build_canonical_keyword_resolver_service()
    )
    app.state.reference_caption_retriever_service = (
        build_reference_caption_retriever_service(
            app.state.canonical_keyword_resolver_service,
            enabled=settings.REFERENCE_CAPTION_RAG_ENABLED,
            max_references=settings.REFERENCE_CAPTION_MAX_REFERENCES,
        )
    )
    app.state.menu_promotion_context_service = (
        build_menu_promotion_context_service()
    )
    logger.info(
        "Keyword extraction configured.",
        extra=build_log_extra(
            "app.startup.keyword_extraction_configured",
            component="startup",
            keyword_model_base_url=keyword_client.base_url,
            keyword_chat_endpoint=keyword_client.chat_endpoint,
            keyword_health_endpoint=keyword_client.health_endpoint,
            keyword_timeout_seconds=keyword_client.timeout_seconds,
        ),
    )
    logger.info(
        "Caption generation configured.",
        extra=build_log_extra(
            "app.startup.caption_generation_configured",
            component="startup",
            caption_model_base_url=caption_client.base_url,
            caption_chat_endpoint=caption_client.chat_endpoint,
            caption_health_endpoint=caption_client.health_endpoint,
            caption_timeout_seconds=caption_client.timeout_seconds,
        ),
    )
    logger.info(
        "Canonical keyword resolver configured.",
        extra=build_log_extra(
            "app.startup.canonical_keyword_resolver_configured",
            component="startup",
            canonical_embedding_model_name=settings.CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME,
            canonical_embedding_dim=settings.CANONICAL_KEYWORD_EMBEDDING_DIM,
            canonical_embedding_cache_dir=str(
                settings.CANONICAL_KEYWORD_EMBEDDING_MODEL_CACHE_DIR
            ),
        ),
    )
    logger.info(
        "Reference caption retriever configured.",
        extra=build_log_extra(
            "app.startup.reference_caption_retriever_configured",
            component="startup",
            reference_caption_rag_enabled=settings.REFERENCE_CAPTION_RAG_ENABLED,
            reference_caption_max_references=settings.REFERENCE_CAPTION_MAX_REFERENCES,
        ),
    )
    logger.info(
        "Menu promotion context service configured.",
        extra=build_log_extra(
            "app.startup.menu_promotion_context_configured",
            component="startup",
        ),
    )

    try:
        await app.state.keyword_extraction_service.preload()
        logger.info(
            "Keyword extraction server connectivity check completed.",
            extra=build_log_extra(
                "app.startup.keyword_preload",
                component="startup",
                stage="keyword_preload",
                outcome="succeeded",
                keyword_model_base_url=keyword_client.base_url,
                keyword_health_endpoint=keyword_client.health_endpoint,
            ),
        )
    except KeywordExtractionUnavailableError as exc:
        logger.warning(
            "Keyword extraction server is unavailable at startup: %s. "
            "The app will continue, but process-utterance may return 503 until the server is reachable.",
            exc,
            exc_info=True,
            extra=build_log_extra(
                "app.startup.keyword_preload",
                component="startup",
                stage="keyword_preload",
                outcome="failed",
                error_type=exc.__class__.__name__,
                keyword_model_base_url=keyword_client.base_url,
                keyword_health_endpoint=keyword_client.health_endpoint,
            ),
        )
    except Exception:
        logger.warning(
            "Keyword extraction server is unavailable at startup. "
            "The app will continue, but process-utterance may return 503 until the server is reachable.",
            exc_info=True,
            extra=build_log_extra(
                "app.startup.keyword_preload",
                component="startup",
                stage="keyword_preload",
                outcome="failed",
                error_type="unexpected_startup_error",
                keyword_model_base_url=keyword_client.base_url,
                keyword_health_endpoint=keyword_client.health_endpoint,
            ),
        )

    try:
        await app.state.caption_generation_service.preload()
        logger.info(
            "Caption generation server connectivity check completed.",
            extra=build_log_extra(
                "app.startup.caption_preload",
                component="startup",
                stage="caption_preload",
                outcome="succeeded",
                caption_model_base_url=caption_client.base_url,
                caption_health_endpoint=caption_client.health_endpoint,
            ),
        )
    except CaptionGenerationUnavailableError as exc:
        logger.warning(
            "Caption generation server is unavailable at startup: %s. "
            "The app will continue and fall back to rule-based caption text until the server is reachable.",
            exc,
            exc_info=True,
            extra=build_log_extra(
                "app.startup.caption_preload",
                component="startup",
                stage="caption_preload",
                outcome="failed",
                error_type=exc.__class__.__name__,
                caption_model_base_url=caption_client.base_url,
                caption_health_endpoint=caption_client.health_endpoint,
            ),
        )
    except Exception:
        logger.warning(
            "Caption generation server is unavailable at startup. "
            "The app will continue and fall back to rule-based caption text until the server is reachable.",
            exc_info=True,
            extra=build_log_extra(
                "app.startup.caption_preload",
                component="startup",
                stage="caption_preload",
                outcome="failed",
                error_type="unexpected_startup_error",
                caption_model_base_url=caption_client.base_url,
                caption_health_endpoint=caption_client.health_endpoint,
            ),
        )

    try:
        await app.state.canonical_keyword_resolver_service.preload()
        logger.info(
            "Canonical keyword resolver preload completed.",
            extra=build_log_extra(
                "app.startup.canonical_keyword_resolver_preload",
                component="startup",
                stage="canonical_keyword_preload",
                outcome="succeeded",
                canonical_embedding_model_name=settings.CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME,
            ),
        )
    except Exception as exc:
        logger.warning(
            "Canonical keyword resolver is unavailable at startup: %s. "
            "The app will continue and fall back to draft keywords for final keyword storage.",
            exc,
            exc_info=True,
            extra=build_log_extra(
                "app.startup.canonical_keyword_resolver_preload",
                component="startup",
                stage="canonical_keyword_preload",
                outcome="failed",
                error_type=exc.__class__.__name__,
                canonical_embedding_model_name=settings.CANONICAL_KEYWORD_EMBEDDING_MODEL_NAME,
            ),
        )

    try:
        await app.state.reference_caption_retriever_service.preload()
        logger.info(
            "Reference caption retriever preload completed.",
            extra=build_log_extra(
                "app.startup.reference_caption_retriever_preload",
                component="startup",
                stage="reference_caption_retriever_preload",
                outcome="succeeded",
                reference_caption_rag_enabled=settings.REFERENCE_CAPTION_RAG_ENABLED,
                reference_caption_max_references=settings.REFERENCE_CAPTION_MAX_REFERENCES,
            ),
        )
    except Exception as exc:
        logger.warning(
            "Reference caption retriever is unavailable at startup: %s. "
            "The app will continue and skip caption RAG until the retriever is reachable.",
            exc,
            exc_info=True,
            extra=build_log_extra(
                "app.startup.reference_caption_retriever_preload",
                component="startup",
                stage="reference_caption_retriever_preload",
                outcome="failed",
                error_type=exc.__class__.__name__,
                reference_caption_rag_enabled=settings.REFERENCE_CAPTION_RAG_ENABLED,
                reference_caption_max_references=settings.REFERENCE_CAPTION_MAX_REFERENCES,
            ),
        )

    try:
        await app.state.menu_promotion_context_service.preload()
        logger.info(
            "Menu promotion context service preload completed.",
            extra=build_log_extra(
                "app.startup.menu_promotion_context_preload",
                component="startup",
                stage="menu_promotion_context_preload",
                outcome="succeeded",
            ),
        )
    except Exception as exc:
        logger.warning(
            "Menu promotion context service is unavailable at startup: %s. "
            "The app will continue and skip menu candidate lookup until the database is reachable.",
            exc,
            exc_info=True,
            extra=build_log_extra(
                "app.startup.menu_promotion_context_preload",
                component="startup",
                stage="menu_promotion_context_preload",
                outcome="failed",
                error_type=exc.__class__.__name__,
            ),
        )

    try:
        await redis.ping()
        logger.info(
            "Redis connectivity check succeeded.",
            extra=build_log_extra(
                "app.startup.redis_ping",
                component="startup",
                stage="redis_ping",
                outcome="succeeded",
            ),
        )
    except Exception:
        logger.warning(
            "Redis connectivity check failed during startup.",
            exc_info=True,
            extra=build_log_extra(
                "app.startup.redis_ping",
                component="startup",
                stage="redis_ping",
                outcome="failed",
                error_type="redis_ping_failed",
            ),
        )

    try:
        yield
    finally:
        logger.info(
            "AI service shutdown started.",
            extra=build_log_extra(
                "app.shutdown.started",
                component="shutdown",
                outcome="started",
                temp_root=str(temp_root),
            ),
        )
        try:
            shutil.rmtree(temp_root, ignore_errors=True)
            logger.info(
                "Temporary workspace cleanup completed.",
                extra=build_log_extra(
                    "app.shutdown.temp_root_cleanup",
                    component="shutdown",
                    stage="temp_root_cleanup",
                    outcome="succeeded",
                    temp_root=str(temp_root),
                ),
            )
        except Exception:
            logger.warning(
                "Temporary workspace cleanup failed.",
                exc_info=True,
                extra=build_log_extra(
                    "app.shutdown.temp_root_cleanup",
                    component="shutdown",
                    stage="temp_root_cleanup",
                    outcome="failed",
                    error_type="temp_root_cleanup_failed",
                    temp_root=str(temp_root),
                ),
            )
        try:
            await close_redis()
            logger.info(
                "Redis client closed.",
                extra=build_log_extra(
                    "app.shutdown.redis_close",
                    component="shutdown",
                    stage="redis_close",
                    outcome="succeeded",
                ),
            )
        except Exception:
            logger.warning(
                "Redis client close failed.",
                exc_info=True,
                extra=build_log_extra(
                    "app.shutdown.redis_close",
                    component="shutdown",
                    stage="redis_close",
                    outcome="failed",
                    error_type="redis_close_failed",
                ),
            )
        try:
            await dispose_engine()
            logger.info(
                "Database engine disposed.",
                extra=build_log_extra(
                    "app.shutdown.dispose_engine",
                    component="shutdown",
                    stage="dispose_engine",
                    outcome="succeeded",
                ),
            )
        except Exception:
            logger.warning(
                "Database engine dispose failed.",
                exc_info=True,
                extra=build_log_extra(
                    "app.shutdown.dispose_engine",
                    component="shutdown",
                    stage="dispose_engine",
                    outcome="failed",
                    error_type="dispose_engine_failed",
                ),
            )


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/ai/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

configure_app_logging(settings.LOG_LEVEL)


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    request_id = request.headers.get("x-request-id") or new_request_id()
    token = set_request_id(request_id)
    request.state.request_id = request_id
    started_at = time.perf_counter()
    raw_body, payload = await _read_request_payload(request)
    route = _route_label(request)
    session_id = _session_id_from_path(request)
    payload_summary = _request_payload_summary(request, payload or {})
    logger.info(
        "HTTP request started.",
        extra=build_log_extra(
            "http.request.started",
            component="http",
            route=route,
            method=request.method,
            session_id=session_id,
            body_size_bytes=len(raw_body),
            outcome="started",
            **payload_summary,
        ),
    )
    try:
        response = await call_next(request)
    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        logger.exception(
            "HTTP request raised an unhandled exception.",
            extra=build_log_extra(
                "http.request.failed",
                component="http",
                route=route,
                method=request.method,
                session_id=session_id,
                elapsed_ms=elapsed_ms,
                outcome="failed",
                error_type=exc.__class__.__name__,
            ),
        )
        reset_request_id(token)
        raise

    elapsed_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info(
        "HTTP request completed.",
        extra=build_log_extra(
            "http.request.completed",
            component="http",
            route=route,
            method=request.method,
            session_id=session_id,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
            outcome="succeeded" if response.status_code < 400 else "failed",
        ),
    )
    response.headers["x-request-id"] = request_id
    reset_request_id(token)
    return response


@app.exception_handler(HTTPException)
async def handle_http_exception(request: Request, exc: HTTPException):
    logger.warning(
        "HTTPException returned to client.",
        extra=build_log_extra(
            "http.exception.http",
            component="http",
            route=_route_label(request),
            method=request.method,
            session_id=_session_id_from_path(request),
            status_code=exc.status_code,
            outcome="failed",
            error_type=exc.__class__.__name__,
            detail=exc.detail,
        ),
    )
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def handle_validation_exception(request: Request, exc: RequestValidationError):
    logger.warning(
        "Request validation failed.",
        extra=build_log_extra(
            "http.exception.validation",
            component="http",
            route=_route_label(request),
            method=request.method,
            session_id=_session_id_from_path(request),
            status_code=422,
            outcome="failed",
            error_type=exc.__class__.__name__,
            validation_error_count=len(exc.errors()),
        ),
    )
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def handle_unexpected_exception(request: Request, exc: Exception):
    logger.exception(
        "Unexpected exception returned as 500.",
        extra=build_log_extra(
            "http.exception.unexpected",
            component="http",
            route=_route_label(request),
            method=request.method,
            session_id=_session_id_from_path(request),
            status_code=500,
            outcome="failed",
            error_type=exc.__class__.__name__,
        ),
    )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

app.include_router(api_router, prefix="/ai")
