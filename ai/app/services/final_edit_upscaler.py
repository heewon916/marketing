from __future__ import annotations

import importlib
import logging
from pathlib import Path
import sys
import threading
from typing import Any

import httpx
import numpy as np

from app.core.config import DEFAULT_REALESRGAN_WEIGHTS_PATH, settings
from app.services.final_edit_runtime import FinalEditUnavailableError

logger = logging.getLogger(__name__)

_DOWNLOAD_TIMEOUT_SECONDS = 120.0
_DOWNLOAD_CHUNK_BYTES = 1024 * 1024
_DEFAULT_TILE_SIZE = 256
_DEFAULT_TILE_PAD = 10
_DEFAULT_PRE_PAD = 0
_upscaler_lock = threading.Lock()
_shared_upscaler: "RealEsrganUpscaler | None" = None
_TORCHVISION_LEGACY_TENSOR_MODULE = "torchvision.transforms.functional_tensor"
_TORCHVISION_FALLBACK_TENSOR_MODULE = "torchvision.transforms._functional_tensor"


def _import_torch() -> Any:
    try:
        import torch
    except (ImportError, ModuleNotFoundError) as exc:
        raise FinalEditUnavailableError(
            "PyTorch is unavailable for final edit upscaling."
        ) from exc
    return torch


def _ensure_torchvision_transform_compat() -> None:
    if _TORCHVISION_LEGACY_TENSOR_MODULE in sys.modules:
        return

    try:
        importlib.import_module(_TORCHVISION_LEGACY_TENSOR_MODULE)
        return
    except ModuleNotFoundError:
        pass

    try:
        compatibility_module = importlib.import_module(
            _TORCHVISION_FALLBACK_TENSOR_MODULE
        )
    except ModuleNotFoundError as exc:
        raise FinalEditUnavailableError(
            "Torchvision tensor transform compatibility is unavailable "
            "for Real-ESRGAN."
        ) from exc

    sys.modules[_TORCHVISION_LEGACY_TENSOR_MODULE] = compatibility_module


def _import_realesrgan_components() -> tuple[type[Any], type[Any]]:
    try:
        _ensure_torchvision_transform_compat()
        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer
    except (ImportError, ModuleNotFoundError) as exc:
        raise FinalEditUnavailableError(
            "Real-ESRGAN runtime is unavailable for final edit."
        ) from exc
    return RRDBNet, RealESRGANer


def ensure_realesrgan_weights_available(weights_path: Path | None = None) -> Path:
    resolved_path = weights_path or DEFAULT_REALESRGAN_WEIGHTS_PATH
    if resolved_path.exists():
        return resolved_path

    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = resolved_path.with_suffix(f"{resolved_path.suffix}.download")
    url = settings.REALESRGAN_WEIGHTS_URL
    logger.info("Real-ESRGAN weights are missing; downloading from %s.", url)
    try:
        with httpx.stream(
            "GET",
            url,
            follow_redirects=True,
            timeout=_DOWNLOAD_TIMEOUT_SECONDS,
        ) as response:
            response.raise_for_status()
            with temp_path.open("wb") as handle:
                for chunk in response.iter_bytes(_DOWNLOAD_CHUNK_BYTES):
                    if chunk:
                        handle.write(chunk)
        temp_path.replace(resolved_path)
    except httpx.HTTPError as exc:
        temp_path.unlink(missing_ok=True)
        resolved_path.unlink(missing_ok=True)
        raise FinalEditUnavailableError(
            f"Failed to download Real-ESRGAN weights from {url}."
        ) from exc

    if not resolved_path.exists() or resolved_path.stat().st_size == 0:
        temp_path.unlink(missing_ok=True)
        resolved_path.unlink(missing_ok=True)
        raise FinalEditUnavailableError(
            f"Downloaded Real-ESRGAN weights are empty or missing at {resolved_path}."
        )
    return resolved_path


class RealEsrganUpscaler:
    def __init__(self, weights_path: Path) -> None:
        torch = _import_torch()
        rrdbnet_class, realesrganer_class = _import_realesrgan_components()
        self._weights_path = weights_path
        self._use_cuda = bool(
            getattr(torch, "cuda", None) is not None and torch.cuda.is_available()
        )
        model = rrdbnet_class(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=23,
            num_grow_ch=32,
            scale=2,
        )
        self._upsampler = realesrganer_class(
            scale=2,
            model_path=str(weights_path),
            model=model,
            tile=_DEFAULT_TILE_SIZE,
            tile_pad=_DEFAULT_TILE_PAD,
            pre_pad=_DEFAULT_PRE_PAD,
            half=self._use_cuda,
            gpu_id=0 if self._use_cuda else None,
        )

    @property
    def weights_path(self) -> Path:
        return self._weights_path

    def upscale(self, image: np.ndarray, scale: int) -> np.ndarray:
        normalized_input = np.ascontiguousarray(image)
        output, _ = self._upsampler.enhance(normalized_input, outscale=2)
        return output


def build_realesrgan_upscaler(weights_path: Path | None = None) -> RealEsrganUpscaler:
    resolved_path = weights_path or DEFAULT_REALESRGAN_WEIGHTS_PATH
    if not resolved_path.exists():
        raise FinalEditUnavailableError(
            f"Real-ESRGAN weights are unavailable at {resolved_path}."
        )
    return RealEsrganUpscaler(resolved_path)


def get_realesrgan_upscaler() -> RealEsrganUpscaler:
    global _shared_upscaler
    if _shared_upscaler is not None:
        return _shared_upscaler

    with _upscaler_lock:
        if _shared_upscaler is None:
            weights_path = ensure_realesrgan_weights_available()
            _shared_upscaler = build_realesrgan_upscaler(weights_path)
    return _shared_upscaler


def ensure_final_edit_upscaler_available() -> Path:
    global _shared_upscaler
    with _upscaler_lock:
        weights_path = ensure_realesrgan_weights_available()
        if _shared_upscaler is None:
            _shared_upscaler = build_realesrgan_upscaler(weights_path)
    return weights_path


def reset_realesrgan_upscaler() -> None:
    global _shared_upscaler
    with _upscaler_lock:
        _shared_upscaler = None
