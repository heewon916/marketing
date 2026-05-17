import sys
import types

import numpy as np
import pytest

from app.services.final_edit_runtime import FinalEditUnavailableError
from app.services.final_edit_upscaler import (
    _TORCHVISION_FALLBACK_TENSOR_MODULE,
    _TORCHVISION_LEGACY_TENSOR_MODULE,
    _ensure_torchvision_transform_compat,
    RealEsrganUpscaler,
)


def test_ensure_torchvision_transform_compat_registers_legacy_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    compatibility_module = types.ModuleType("functional_tensor_compat")

    def fake_import_module(name: str):
        if name == _TORCHVISION_LEGACY_TENSOR_MODULE:
            raise ModuleNotFoundError(name)
        if name == _TORCHVISION_FALLBACK_TENSOR_MODULE:
            return compatibility_module
        raise AssertionError(f"unexpected import: {name}")

    monkeypatch.delitem(
        sys.modules,
        _TORCHVISION_LEGACY_TENSOR_MODULE,
        raising=False,
    )
    monkeypatch.setattr("app.services.final_edit_upscaler.importlib.import_module", fake_import_module)

    _ensure_torchvision_transform_compat()

    assert sys.modules[_TORCHVISION_LEGACY_TENSOR_MODULE] is compatibility_module


def test_ensure_torchvision_transform_compat_raises_without_compatible_module(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_import_module(name: str):
        raise ModuleNotFoundError(name)

    monkeypatch.delitem(
        sys.modules,
        _TORCHVISION_LEGACY_TENSOR_MODULE,
        raising=False,
    )
    monkeypatch.setattr("app.services.final_edit_upscaler.importlib.import_module", fake_import_module)

    with pytest.raises(
        FinalEditUnavailableError,
        match="Torchvision tensor transform compatibility is unavailable",
    ):
        _ensure_torchvision_transform_compat()


def test_realesrgan_upscale_uses_native_two_x_output() -> None:
    image = np.zeros((8, 8, 3), dtype=np.uint8)
    expected = np.zeros((16, 16, 3), dtype=np.uint8)
    calls: list[tuple[tuple[int, ...], int]] = []

    class FakeUpsampler:
        def enhance(self, normalized_input, outscale):
            calls.append((normalized_input.shape, outscale))
            return expected, None

    upscaler = RealEsrganUpscaler.__new__(RealEsrganUpscaler)
    upscaler._upsampler = FakeUpsampler()

    result = upscaler.upscale(image, scale=4)

    assert calls == [((8, 8, 3), 2)]
    assert result is expected
