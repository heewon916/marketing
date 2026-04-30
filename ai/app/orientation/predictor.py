"""Lazy orientation predictor based on the referenced Deep-OAD flow."""

from __future__ import annotations

import logging
from pathlib import Path
import threading

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class OrientationPredictor:
    """Predict and correct image orientation using a lazily loaded model."""

    def __init__(
        self,
        model_name: str = "vit",
        weights_path: str | Path | None = None,
    ) -> None:
        self.model_name = model_name
        self.weights_path = Path(weights_path) if weights_path else None
        self._model = None
        self._processor = None
        self._lock = threading.Lock()

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

        with self._lock:
            if self._model is not None:
                return self._model

            if self.model_name != "vit":
                raise RuntimeError(f"Unsupported orientation model: {self.model_name}")
            if self.weights_path is None:
                raise RuntimeError("Orientation model weights path is unavailable.")
            if not self.weights_path.exists():
                raise RuntimeError(
                    f"Orientation model weights file does not exist: {self.weights_path}"
                )

            try:
                import tensorflow as tf
                from transformers import AutoImageProcessor, TFAutoModel
            except ImportError as exc:
                raise RuntimeError(
                    "TensorFlow and transformers are required for orientation correction "
                    "but are not installed."
                ) from exc

            try:
                image_size = 224
                vit_base = self._load_vit_base_model(TFAutoModel)
                img_input = tf.keras.layers.Input(shape=(3, image_size, image_size))
                vit_output = vit_base(img_input)
                angle_output = tf.keras.layers.Dense(1, activation="linear")(
                    vit_output[-1]
                )
                model = tf.keras.Model(img_input, angle_output)
                model.load_weights(self.weights_path)
                self._model = model
                self._processor = AutoImageProcessor.from_pretrained(
                    "google/vit-base-patch16-224"
                )
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to initialize orientation model from {self.weights_path}: {exc}"
                ) from exc

        return self._model

    def _load_vit_base_model(self, tf_auto_model):
        model_id = "google/vit-base-patch16-224"

        try:
            return tf_auto_model.from_pretrained(model_id)
        except TypeError as exc:
            if "safe_open" not in str(exc):
                raise

            logger.warning(
                "Retrying ViT backbone load without safetensors after safe_open failure.",
                extra={"model_id": model_id},
            )
            return tf_auto_model.from_pretrained(model_id, use_safetensors=False)

    def _preprocess(self, image_path: Path) -> np.ndarray:
        if self._processor is None:
            self._load_model()

        with Image.open(image_path) as image:
            rgb_image = image.convert("RGB").resize((224, 224))
            array = np.asarray(rgb_image)

        processed = self._processor(images=[array], return_tensors="np")
        return np.asarray(processed["pixel_values"], dtype=np.float32)
