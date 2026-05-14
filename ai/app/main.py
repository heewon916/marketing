import json
import logging
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
from app.bootstrap import lifespan
from app.core.config import settings
from app.logging import (
    build_log_extra,
    configure_app_logging,
    new_request_id,
    preview_text,
    reset_request_id,
    set_request_id,
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
