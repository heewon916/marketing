"""Video processor implementations used by the frame extractor."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from app.perfectframe.schemas import Image, Images

TARGET_SAMPLE_FPS = 30


def _import_cv2():
    try:
        import cv2  # type: ignore[import-not-found]
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "opencv-python-headless is required for frame extraction."
        ) from exc
    return cv2


class VideoProcessor(ABC):
    """Abstract video processor."""

    @classmethod
    @abstractmethod
    def get_next_frames(
        cls, video_path: Path, frames_batch_size: int
    ) -> Generator[Images, None, None]:
        """Yield batches of frames from a video."""


class OpenCVVideo(VideoProcessor):
    """OpenCV-based frame sampler."""

    class Error(Exception):
        """Raised when a video cannot be processed."""

    @staticmethod
    @contextmanager
    def _video_capture(video_path: Path):
        cv2 = _import_cv2()
        video_cap = cv2.VideoCapture(str(video_path))
        try:
            if not video_cap.isOpened():
                raise OpenCVVideo.Error(f"Can't open video file: {video_path}")
            yield video_cap
        finally:
            video_cap.release()

    @classmethod
    def get_next_frames(
        cls, video_path: Path, frames_batch_size: int
    ) -> Generator[Images, None, None]:
        cv2 = _import_cv2()
        with cls._video_capture(video_path) as video:
            frame_rate = cls._get_video_property(video, cv2.CAP_PROP_FPS)
            total_frames = cls._get_video_property(video, cv2.CAP_PROP_FRAME_COUNT)
            sampling_step = cls._get_sampling_step(frame_rate)

            frames_batch: Images = []
            for frame_index in range(0, total_frames, sampling_step):
                frame = cls._read_next_frame(video, frame_index)
                if frame is None:
                    continue
                frames_batch.append(frame)
                if len(frames_batch) == frames_batch_size:
                    yield frames_batch
                    frames_batch = []

            if frames_batch:
                yield frames_batch

    @classmethod
    def _read_next_frame(cls, video, frame_index: int) -> Image | None:
        cv2 = _import_cv2()
        video.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        success, frame = video.read()
        if not success:
            return None
        return frame

    @staticmethod
    def _get_sampling_step(frame_rate: int) -> int:
        # Cap sampling at 30 frames per second while keeping lower-FPS videos intact.
        return max(1, round(frame_rate / TARGET_SAMPLE_FPS))

    @staticmethod
    def _get_video_property(video, property_id: int) -> int:
        property_value = video.get(property_id)
        if property_value <= 0:
            raise ValueError(f"Invalid video property value retrieved: {property_value}.")
        return round(property_value)
