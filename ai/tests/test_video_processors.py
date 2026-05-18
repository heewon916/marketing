from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import numpy as np
import pytest

from app.perfectframe.video_processors import OpenCVVideo


def test_get_sampling_step_samples_60fps_video_at_30fps() -> None:
    assert OpenCVVideo._get_sampling_step(60) == 2


def test_get_sampling_step_keeps_30fps_video_at_every_frame() -> None:
    assert OpenCVVideo._get_sampling_step(30) == 1


def test_get_sampling_step_keeps_lower_fps_video_at_every_frame() -> None:
    assert OpenCVVideo._get_sampling_step(24) == 1


def test_normalize_frame_rate_falls_back_for_invalid_or_extreme_values() -> None:
    assert OpenCVVideo._normalize_frame_rate(None) == 30
    assert OpenCVVideo._normalize_frame_rate(0) == 30
    assert OpenCVVideo._normalize_frame_rate(1000) == 30


def test_normalize_frame_count_returns_none_for_invalid_values() -> None:
    assert OpenCVVideo._normalize_frame_count(None) is None
    assert OpenCVVideo._normalize_frame_count(-1) is None
    assert OpenCVVideo._normalize_frame_count(20_000_000) is None


def test_sequential_fallback_yields_sampled_frames() -> None:
    class FakeVideo:
        def __init__(self) -> None:
            self.index = 0

        def read(self):
            if self.index >= 5:
                return False, None
            frame = np.full((2, 2, 3), self.index, dtype=np.uint8)
            self.index += 1
            return True, frame

    batches = list(
        OpenCVVideo._yield_sampled_frames_sequentially(
            FakeVideo(),
            sampling_step=2,
            frames_batch_size=2,
        )
    )

    assert len(batches) == 2
    assert [int(frame[0, 0, 0]) for frame in batches[0]] == [0, 2]
    assert [int(frame[0, 0, 0]) for frame in batches[1]] == [4]


def test_metadata_path_records_scan_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeVideo:
        def __init__(self) -> None:
            self.positions: list[int] = []

        def isOpened(self) -> bool:
            return True

        def release(self) -> None:
            return None

        def get(self, property_id: int) -> float:
            if property_id == 5:
                return 60.0
            if property_id == 7:
                return 120.0
            return 0.0

        def set(self, property_id: int, value: int) -> None:
            self.positions.append(value)

        def read(self):
            return True, np.zeros((2, 2, 3), dtype=np.uint8)

    @contextmanager
    def fake_capture(_video_path):
        yield FakeVideo()

    monkeypatch.setattr(OpenCVVideo, "_video_capture", fake_capture)
    batches = list(OpenCVVideo.get_next_frames(Path("dummy.webm"), frames_batch_size=2))

    assert len(batches) >= 1
    assert OpenCVVideo.last_scan_metadata["video_frame_scan_mode"] == "metadata"
    assert OpenCVVideo.last_scan_metadata["video_fps_effective"] == 60
    assert OpenCVVideo.last_scan_metadata["video_sampling_step"] == 2


def test_sequential_fallback_records_scan_metadata(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeVideo:
        def __init__(self) -> None:
            self.index = 0

        def isOpened(self) -> bool:
            return True

        def release(self) -> None:
            return None

        def get(self, property_id: int) -> float:
            if property_id == 5:
                return 1000.0
            if property_id == 7:
                return -9.223372036854776e18
            return 0.0

        def read(self):
            if self.index >= 3:
                return False, None
            frame = np.full((2, 2, 3), self.index, dtype=np.uint8)
            self.index += 1
            return True, frame

    @contextmanager
    def fake_capture(_video_path):
        yield FakeVideo()

    monkeypatch.setattr(OpenCVVideo, "_video_capture", fake_capture)
    batches = list(OpenCVVideo.get_next_frames(Path("dummy.webm"), frames_batch_size=4))

    assert len(batches) == 1
    assert len(batches[0]) == 3
    assert OpenCVVideo.last_scan_metadata["video_frame_scan_mode"] == "sequential_fallback"
    assert OpenCVVideo.last_scan_metadata["video_fps_effective"] == 30
    assert OpenCVVideo.last_scan_metadata["video_sampling_step"] == 1
