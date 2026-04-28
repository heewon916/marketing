from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
import shutil
from tempfile import mkdtemp

from fastapi import FastAPI
from fastapi.routing import APIRoute

from app.api.main import api_router
from app.core.config import settings
from app.db.postgres import dispose_engine
from app.db.redis import close_redis, get_redis_client
from app.perfectframe.dependencies import get_dependencies
from app.perfectframe.extractors import BestFrameExtractor
from app.perfectframe.schemas import ExtractorConfig
from app.services.frame_extraction import FrameExtractionService, S3DraftUploader


def custom_generate_unique_id(route: APIRoute) -> str:
    tag = route.tags[0] if route.tags else "default"
    return f"{tag}-{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis = get_redis_client()
    temp_root = Path(mkdtemp(prefix="ai-frame-extractor-"))
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
        uploader=S3DraftUploader(),
        temp_root=temp_root,
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

app.include_router(api_router, prefix="/ai")
