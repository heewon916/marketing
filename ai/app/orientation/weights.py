"""Helpers for provisioning orientation model weights."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


async def ensure_orientation_weights_available() -> Path:
    """Ensure the configured orientation weights file exists locally."""

    weights_path = settings.orientation_model_weights_path
    if weights_path.exists():
        return weights_path

    weights_path.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(_download_orientation_weights, weights_path)
    return weights_path


def _download_orientation_weights(weights_path: Path) -> None:
    try:
        import gdown
    except ImportError as exc:
        raise RuntimeError(
            "gdown is required to auto-download orientation model weights."
        ) from exc

    logger.info(
        "Orientation model weights are missing; downloading from Google Drive.",
        extra={"weights_path": str(weights_path)},
    )
    output = gdown.download(
        url=settings.ORIENTATION_MODEL_DOWNLOAD_URL,
        output=str(weights_path),
        quiet=False,
        fuzzy=True,
    )
    if output is None or not weights_path.exists():
        raise RuntimeError(
            f"Failed to download orientation model weights to {weights_path}."
        )
