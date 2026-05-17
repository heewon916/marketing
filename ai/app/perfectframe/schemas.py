"""Define minimal PerfectFrameAI-compatible schemas."""

from enum import Enum
from pathlib import Path
from typing import NamedTuple

import numpy as np
from pydantic import BaseModel, DirectoryPath, Field


class ImageResolution(NamedTuple):
    """Resolution of an image in pixels."""

    width: int
    height: int


Image = np.ndarray
Images = list[Image]
ImagesBatch = np.ndarray
ScoresArray = np.ndarray


class FileExtension(str, Enum):
    """Base class for supported file extensions."""

    @classmethod
    def contains(cls, value: str) -> bool:
        return value in cls._value2member_map_


class ImageExtension(FileExtension):
    """Supported image file extensions."""

    JPG = ".jpg"
    PNG = ".png"


class VideoExtension(FileExtension):
    """Supported video file extensions."""

    MP4 = ".mp4"
    MOV = ".mov"
    WEBM = ".webm"
    MKV = ".mkv"
    AVI = ".avi"
    WMV = ".wmv"
    FLV = ".flv"
    M4V = ".m4v"


class ExtractorConfig(BaseModel):
    """Configuration for the best-frame extractor."""

    input_directory: DirectoryPath
    output_directory: DirectoryPath
    processed_video_prefix: str = "frames_extracted_"
    batch_size: int = Field(default=100, ge=1)
    comparing_group_size: int = Field(default=5, ge=1)
    top_images_percent: float = 90.0
    images_output_format: ImageExtension = ImageExtension.PNG
    input_size: ImageResolution = ImageResolution(224, 224)
    weights_directory: Path | str = Path.home() / ".cache" / "huggingface"
    weights_filename: str = "weights.onnx"
    weights_repo_url: str = "https://huggingface.co/BKDDFS/nima_weights/resolve/main/"
    all_frames: bool = False
