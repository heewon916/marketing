"""Image scorers used by the frame extractor."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np

from app.logging import build_log_extra
from app.perfectframe.schemas import ImagesBatch

logger = logging.getLogger(__name__)


class ImageEvaluator(ABC):
    """Abstract image evaluator."""

    @abstractmethod
    def evaluate_images(self, normalized_images: ImagesBatch) -> list[float]:
        """Return a score for each image."""


class NIMAEvaluator(ImageEvaluator):
    """NIMA-based aesthetic evaluator using ONNX runtime."""

    _prediction_weights = np.arange(1, 11)
    _weights_sum = float(_prediction_weights.sum())

    def __init__(self, weights_path: Path) -> None:
        import onnxruntime as ort

        self._session = ort.InferenceSession(str(weights_path))
        self._input_name = self._session.get_inputs()[0].name

    def evaluate_images(self, normalized_images: ImagesBatch) -> list[float]:
        predictions = self._session.run(
            None,
            {self._input_name: normalized_images.astype(np.float32)},
        )[0]
        if not isinstance(predictions, np.ndarray):
            return []
        return [self._calculate_weighted_mean(prediction) for prediction in predictions]

    def _calculate_weighted_mean(self, prediction: np.ndarray) -> float:
        return float(np.sum(prediction * self._prediction_weights) / self._weights_sum)


def build_image_evaluator(weights_path: Path | None) -> ImageEvaluator:
    """Return a NIMA evaluator when weights are usable, sharpness fallback otherwise."""

    if weights_path is None or not weights_path.exists():
        logger.warning(
            "NIMA weights unavailable; falling back to sharpness scorer.",
            extra=build_log_extra(
                "app.startup.nima_evaluator.fallback",
                component="startup",
                stage="nima_evaluator_init",
                outcome="fallback",
                error_type="weights_missing",
                weights_path=str(weights_path) if weights_path else None,
            ),
        )
        return SharpnessVarianceEvaluator()

    try:
        evaluator = NIMAEvaluator(weights_path)
    except Exception as exc:
        logger.warning(
            "NIMA evaluator init failed; falling back to sharpness scorer.",
            exc_info=True,
            extra=build_log_extra(
                "app.startup.nima_evaluator.fallback",
                component="startup",
                stage="nima_evaluator_init",
                outcome="fallback",
                error_type=exc.__class__.__name__,
                weights_path=str(weights_path),
            ),
        )
        return SharpnessVarianceEvaluator()

    logger.info(
        "NIMA evaluator initialized.",
        extra=build_log_extra(
            "app.startup.nima_evaluator.ready",
            component="startup",
            stage="nima_evaluator_init",
            outcome="succeeded",
            weights_path=str(weights_path),
        ),
    )
    return evaluator


# ---------------------------------------------------------------------------
# Automatic fallback target. Activated by build_image_evaluator() when NIMA
# weights are unavailable or ONNX session init fails. Not imported elsewhere.
# ---------------------------------------------------------------------------
class SharpnessVarianceEvaluator(ImageEvaluator):
    """Lightweight edge-variance scorer previously used in place of NIMA."""

    def evaluate_images(self, normalized_images: ImagesBatch) -> list[float]:
        scores: list[float] = []
        for image in normalized_images:
            gray = image.mean(axis=2) if image.ndim == 3 else image
            dx = np.diff(gray, axis=1)
            dy = np.diff(gray, axis=0)
            scores.append(float(np.var(dx) + np.var(dy)))
        return scores
