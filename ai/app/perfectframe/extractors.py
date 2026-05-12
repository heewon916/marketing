"""Provide a minimal BestFrameExtractor compatible with PerfectFrameAI."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.perfectframe.image_evaluators import ImageEvaluator
from app.perfectframe.image_processors import ImageProcessor
from app.perfectframe.schemas import ExtractorConfig, Image, Images, ScoresArray
from app.perfectframe.video_processors import VideoProcessor


class BestFrameExtractor:
    """Extractor that selects the single highest-scoring frame from a video."""

    def __init__(
        self,
        config: ExtractorConfig,
        image_processor: type[ImageProcessor],
        video_processor: type[VideoProcessor],
        image_evaluator: ImageEvaluator,
    ) -> None:
        self._config = config
        self._image_processor = image_processor
        self._video_processor = video_processor
        self._image_evaluator = image_evaluator

    def extract_best_frame(self, video_path: Path) -> tuple[Image, float] | None:
        best_frame: Image | None = None
        best_score: float | None = None

        frames_batch_generator = self._video_processor.get_next_frames(
            video_path,
            self._config.batch_size,
        )
        for frames in frames_batch_generator:
            if not frames:
                continue
            frame, score = self._get_best_frame(frames)
            if frame is None or score is None:
                continue
            if best_score is None or score > best_score:
                best_frame = frame
                best_score = score

        if best_frame is None or best_score is None:
            return None
        return best_frame, best_score

    def _get_best_frame(self, frames: Images) -> tuple[Image | None, float | None]:
        normalized_images = self._image_processor.normalize_images(
            frames,
            self._config.input_size,
        )
        scores = self._evaluate_images(normalized_images)
        if len(scores) == 0:
            return None, None

        best_index = int(np.argmax(scores))
        return frames[best_index], float(scores[best_index])

    def _evaluate_images(self, normalized_images) -> ScoresArray:
        return np.array(self._image_evaluator.evaluate_images(normalized_images))


BestFramesExtractor = BestFrameExtractor
