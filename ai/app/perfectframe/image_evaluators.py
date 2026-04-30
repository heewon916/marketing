"""Image scorers used by the frame extractor."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from app.perfectframe.schemas import ExtractorConfig, ImagesBatch


class ImageEvaluator(ABC):
    """Abstract image evaluator."""

    def __init__(self, config: ExtractorConfig) -> None:
        self._config = config

    @abstractmethod
    def evaluate_images(self, normalized_images: ImagesBatch) -> list[float]:
        """Return a score for each image."""


class NIMAEvaluator(ImageEvaluator):
    """A lightweight sharpness-based scorer standing in for the original evaluator."""

    def evaluate_images(self, normalized_images: ImagesBatch) -> list[float]:
        scores: list[float] = []
        for image in normalized_images:
            gray = image.mean(axis=2) if image.ndim == 3 else image
            dx = np.diff(gray, axis=1)
            dy = np.diff(gray, axis=0)
            scores.append(float(np.var(dx) + np.var(dy)))
        return scores
