from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
import logging
from pathlib import Path
import shutil
from tempfile import mkdtemp

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api.main import api_router
from app.core.config import settings
from app.db.postgres import dispose_engine
from app.db.redis import close_redis, get_redis_client
from app.orientation.predictor import OrientationPredictor
from app.orientation.weights import ensure_orientation_weights_available
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
from app.services.keyword_extraction import (
    KeywordExtractionUnavailableError,
    build_keyword_extraction_service,
)

logger = logging.getLogger(__name__)


def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"


def configure_app_logging() -> None:
    app_logger = logging.getLogger("app")
    level_name = settings.LOG_LEVEL.upper()
    level = getattr(logging, level_name, logging.INFO)

    app_logger.setLevel(level)

    if app_logger.handlers:
        return

    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(
        logging.Formatter(
            "%(levelname)s:%(name)s:%(message)s | "
            "session_id=%(session_id)s final_index=%(final_index)s "
            "draft_key=%(draft_key)s predicted_angle=%(predicted_angle)s "
            "applied_rotation=%(applied_rotation)s",
            defaults={
                "session_id": "-",
                "final_index": "-",
                "draft_key": "-",
                "predicted_angle": "-",
                "applied_rotation": "-",
            },
        )
    )
    app_logger.addHandler(handler)
    app_logger.propagate = False


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis = get_redis_client()
    temp_root = Path(mkdtemp(prefix="ai-frame-extractor-"))
    orientation_weights_path = settings.orientation_model_weights_path
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

    try:
        orientation_weights_path = await ensure_orientation_weights_available()
    except Exception:
        orientation_weights_path = settings.orientation_model_weights_path
        logger.warning(
            "Orientation weights are unavailable at startup. "
            "The app will continue, but final-edit may fail until weights are present.",
            exc_info=True,
            extra={"weights_path": str(orientation_weights_path)},
        )

    app.state.final_edit_service = FinalEditService(
        predictor=OrientationPredictor(
            model_name=settings.ORIENTATION_MODEL_NAME,
            weights_path=str(orientation_weights_path),
        ),
        downloader=S3DraftImageDownloader(),
        uploader=S3FinalImageUploader(),
        temp_root=temp_root / "final-edit",
    )
    app.state.keyword_extraction_service = build_keyword_extraction_service()
    logger.info(
        "Keyword extraction configured.",
        extra={
            "keyword_model_repo_id": settings.KEYWORD_MODEL_HF_REPO_ID,
            "keyword_model_filename": settings.KEYWORD_MODEL_HF_FILENAME,
            "keyword_model_path": str(settings.keyword_model_path),
            "keyword_model_gpu_layers": settings.KEYWORD_MODEL_GPU_LAYERS,
        },
    )

    try:
        await app.state.keyword_extraction_service.preload()
    except KeywordExtractionUnavailableError as exc:
        logger.warning(
            "Keyword extraction model is unavailable at startup: %s. "
            "The app will continue, but process-utterance may return 503 until the model is ready.",
            exc,
            exc_info=True,
        )
    except Exception:
        logger.warning(
            "Keyword extraction model is unavailable at startup. "
            "The app will continue, but process-utterance may return 503 until the model is ready.",
            exc_info=True,
        )

    try:
        await redis.ping()
    except Exception:
        pass

    try:
        yield
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
        await close_redis()
        await dispose_engine()


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url="/ai/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

configure_app_logging()

app.include_router(api_router, prefix="/ai")
