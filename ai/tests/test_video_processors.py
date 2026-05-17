from __future__ import annotations

from app.perfectframe.video_processors import OpenCVVideo


def test_get_sampling_step_samples_60fps_video_at_30fps() -> None:
    assert OpenCVVideo._get_sampling_step(60) == 2


def test_get_sampling_step_keeps_30fps_video_at_every_frame() -> None:
    assert OpenCVVideo._get_sampling_step(30) == 1


def test_get_sampling_step_keeps_lower_fps_video_at_every_frame() -> None:
    assert OpenCVVideo._get_sampling_step(24) == 1
