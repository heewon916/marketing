"""Lazy orientation predictor based on the referenced Deep-OAD flow."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


class OrientationPredictor:
    """Predict and correct image orientation using a lazily loaded model."""

    def __init__(
        self,
        model_name: str = "vit",
        weights_path: str | None = None,
    ) -> None:
        self.model_name = model_name
        self.weights_path = Path(weights_path) if weights_path else None
        self._model = None

    def predict_angle(self, image_path: Path) -> float:
        model = self._load_model()
        inputs = self._preprocess(image_path)
        prediction = model.predict(inputs, verbose=0)
        angle = float(np.asarray(prediction).reshape(-1)[0])
        return angle % 360.0

    def correct_orientation(
        self,
        source_path: Path,
        destination_path: Path,
        predicted_angle: float,
    ) -> Path:
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source_path) as image:
            corrected = image.convert("RGB").rotate(-predicted_angle, expand=True)
            corrected.save(destination_path, format="JPEG")
        return destination_path

    def _load_model(self):
        if self._model is not None:
            return self._model

        if self.model_name != "vit":
            raise RuntimeError(f"Unsupported orientation model: {self.model_name}")
        if self.weights_path is None:
            raise RuntimeError("ORIENTATION_MODEL_WEIGHTS_PATH is not configured.")
        if not self.weights_path.exists():
            raise RuntimeError(
                f"Orientation model weights file does not exist: {self.weights_path}"
            )

        try:
            import tensorflow as tf
        except ImportError as exc:
            raise RuntimeError(
                "TensorFlow is required for orientation correction but is not installed."
            ) from exc

        try:
            self._model = tf.keras.models.load_model(
                self.weights_path,
                compile=False,
            )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to load orientation model from {self.weights_path}: {exc}"
            ) from exc

        return self._model

    @staticmethod
    def _preprocess(image_path: Path) -> np.ndarray:
        with Image.open(image_path) as image:
            resized = image.convert("RGB").resize((224, 224))
            array = np.asarray(resized, dtype=np.float32) / 255.0

        array = (array - 0.5) / 0.5
        return np.expand_dims(array, axis=0)
