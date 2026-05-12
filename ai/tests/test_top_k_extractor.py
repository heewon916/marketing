from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from app.perfectframe.extractors import BestFrameExtractor
from app.perfectframe.image_evaluators import ImageEvaluator
from app.perfectframe.image_processors import ImageProcessor
from app.perfectframe.schemas import ExtractorConfig, ImageResolution
from app.perfectframe.video_processors import VideoProcessor


class _StaticVideoProcessor(VideoProcessor):
    """Yield a fixed sequence of frame batches regardless of video path."""

    batches: list[list[np.ndarray]] = []

    @classmethod
    def get_next_frames(cls, video_path: Path, frames_batch_size: int):
        for batch in cls.batches:
            yield batch


class _PassThroughImageProcessor(ImageProcessor):
    """Skip resizing — frames are already tagged by their pixel value."""

    @staticmethod
    def normalize_images(images, target_size):
        return np.array(images)

    @staticmethod
    def save_image(*args, **kwargs):  # pragma: no cover - unused in these tests
        raise NotImplementedError


class _ScoreByPixelEvaluator(ImageEvaluator):
    """Use the (0,0,0) pixel of each frame as its aesthetic score."""

    def evaluate_images(self, normalized_images):
        return [float(image[0, 0, 0]) for image in normalized_images]


def _make_frame(score_tag: int) -> np.ndarray:
    return np.full((4, 4, 3), score_tag, dtype=np.uint8)


def _make_extractor(batches: list[list[np.ndarray]]) -> BestFrameExtractor:
    _StaticVideoProcessor.batches = batches
    config = ExtractorConfig(
        input_directory=Path("."),
        output_directory=Path("."),
        batch_size=10,
        input_size=ImageResolution(4, 4),
    )
    return BestFrameExtractor(
        config,
        _PassThroughImageProcessor,
        _StaticVideoProcessor,
        _ScoreByPixelEvaluator(),
    )


def test_extract_top_k_frames_returns_top_three_in_descending_order() -> None:
    batches = [
        [_make_frame(s) for s in (1, 9, 4)],
        [_make_frame(s) for s in (7, 2, 8)],
        [_make_frame(s) for s in (5, 6, 3)],
    ]
    extractor = _make_extractor(batches)

    results = extractor.extract_top_k_frames(Path("dummy.mp4"), k=3)

    assert [score for _, score in results] == [9.0, 8.0, 7.0]
    for frame, score in results:
        assert int(frame[0, 0, 0]) == int(score)


def test_extract_top_k_frames_returns_fewer_when_not_enough_frames() -> None:
    batches = [[_make_frame(2), _make_frame(5)]]
    extractor = _make_extractor(batches)

    results = extractor.extract_top_k_frames(Path("dummy.mp4"), k=3)

    assert [score for _, score in results] == [5.0, 2.0]


def test_extract_top_k_frames_returns_empty_when_k_is_zero() -> None:
    batches = [[_make_frame(1), _make_frame(2)]]
    extractor = _make_extractor(batches)

    assert extractor.extract_top_k_frames(Path("dummy.mp4"), k=0) == []


def test_extract_top_k_frames_returns_empty_when_video_has_no_frames() -> None:
    extractor = _make_extractor([])
    assert extractor.extract_top_k_frames(Path("dummy.mp4"), k=3) == []


def test_extract_top_k_frames_skips_empty_batches() -> None:
    batches = [
        [],
        [_make_frame(3), _make_frame(8)],
        [],
        [_make_frame(6)],
    ]
    extractor = _make_extractor(batches)

    results = extractor.extract_top_k_frames(Path("dummy.mp4"), k=2)

    assert [score for _, score in results] == [8.0, 6.0]


@pytest.mark.parametrize("k", [1, 2, 3, 5, 10])
def test_extract_top_k_frames_is_globally_optimal_across_batches(k: int) -> None:
    rng = np.random.default_rng(seed=k)
    raw_scores = rng.integers(0, 100, size=25).tolist()
    batches = [[_make_frame(int(s)) for s in raw_scores[i : i + 5]] for i in range(0, 25, 5)]
    extractor = _make_extractor(batches)

    results = extractor.extract_top_k_frames(Path("dummy.mp4"), k=k)
    expected = sorted(raw_scores, reverse=True)[:k]

    assert [score for _, score in results] == [float(s) for s in expected]
