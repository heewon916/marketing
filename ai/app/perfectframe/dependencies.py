"""Minimal dependency bundle for PerfectFrameAI-compatible extractors."""

from dataclasses import dataclass

from app.perfectframe.image_evaluators import NIMAEvaluator
from app.perfectframe.image_processors import OpenCVImage
from app.perfectframe.schemas import ExtractorConfig
from app.perfectframe.video_processors import OpenCVVideo


@dataclass
class Dependencies:
    """Dependencies required to construct the extractor."""

    image_processor: type[OpenCVImage]
    video_processor: type[OpenCVVideo]
    evaluator: type[NIMAEvaluator]
    config: ExtractorConfig


def get_dependencies(config: ExtractorConfig) -> Dependencies:
    """Return the dependencies required for the extractor."""

    return Dependencies(
        image_processor=OpenCVImage,
        video_processor=OpenCVVideo,
        evaluator=NIMAEvaluator,
        config=config,
    )
