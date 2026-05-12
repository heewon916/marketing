"""Helpers for provisioning NIMA aesthetic-scoring model weights."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx

from app.core.config import DEFAULT_NIMA_WEIGHTS_PATH, settings

logger = logging.getLogger(__name__)

_DOWNLOAD_TIMEOUT_SECONDS = 60.0
_DOWNLOAD_CHUNK_BYTES = 1024 * 1024


class NimaWeightsUnavailableError(RuntimeError):
    """Raised when NIMA model weights cannot be fetched or located."""


async def ensure_nima_weights_available() -> Path:
    """Return the local path to NIMA weights, downloading them if needed."""

    weights_path = DEFAULT_NIMA_WEIGHTS_PATH
    if weights_path.exists():
        return weights_path

    weights_path.parent.mkdir(parents=True, exist_ok=True)
    await asyncio.to_thread(_download_nima_weights, weights_path)
    return weights_path


def _download_nima_weights(weights_path: Path) -> None:
    url = settings.NIMA_WEIGHTS_URL
    logger.info(
        "NIMA weights are missing; downloading from %s.",
        url,
    )
    try:
        with httpx.stream(
            "GET",
            url,
            follow_redirects=True,
            timeout=_DOWNLOAD_TIMEOUT_SECONDS,
        ) as response:
            response.raise_for_status()
            with weights_path.open("wb") as handle:
                for chunk in response.iter_bytes(_DOWNLOAD_CHUNK_BYTES):
                    if chunk:
                        handle.write(chunk)
    except httpx.HTTPError as exc:
        weights_path.unlink(missing_ok=True)
        raise NimaWeightsUnavailableError(
            f"Failed to download NIMA weights from {url}: {exc}"
        ) from exc

    if not weights_path.exists() or weights_path.stat().st_size == 0:
        weights_path.unlink(missing_ok=True)
        raise NimaWeightsUnavailableError(
            f"Downloaded NIMA weights are empty or missing at {weights_path}."
        )
