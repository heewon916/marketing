from __future__ import annotations


class FinalEditUnavailableError(RuntimeError):
    """Raised when the final-edit feature is unavailable."""


def import_cv2():
    try:
        import cv2  # type: ignore[import-not-found]
    except (ImportError, ModuleNotFoundError) as exc:
        raise FinalEditUnavailableError(
            "OpenCV is unavailable for final edit."
        ) from exc
    return cv2


def summarize_unavailable_reason(exc: BaseException) -> str:
    message = str(exc).strip()
    if message:
        return f"{exc.__class__.__name__}: {message}"
    return exc.__class__.__name__
