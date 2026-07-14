from __future__ import annotations

"""Abstract base class for image effects."""

from abc import ABC, abstractmethod
from typing import Any

from gesturevision.core.types import BGRImage, EffectContext, QualityTier


class BaseEffect(ABC):
    """Base implementation shared by classical and AI effects."""

    name: str
    default_params: dict[str, Any]

    def __init__(self, params: dict[str, Any] | None = None) -> None:
        self._params = {**self.default_params, **(params or {})}

    @property
    def params(self) -> dict[str, Any]:
        return dict(self._params)

    def set_param(self, key: str, value: Any) -> None:
        self._params[key] = value

    def supports_realtime(self) -> bool:
        return True

    @abstractmethod
    def apply(self, ctx: EffectContext) -> BGRImage:
        """Transform the input frame and return the result."""

    def _merged_params(self, ctx: EffectContext) -> dict[str, Any]:
        merged = dict(self._params)
        merged.update(ctx.params)
        return merged

    def _processing_frame(self, ctx: EffectContext) -> tuple[BGRImage, float]:
        """
        Optionally downscale for preview quality.

        Returns the frame to process and a scale factor to restore full size.
        """
        frame = ctx.frame
        if ctx.quality != "preview" or frame.shape[1] <= 640:
            return frame, 1.0

        scale = 640 / frame.shape[1]
        height = max(1, int(frame.shape[0] * scale))
        import cv2

        resized = cv2.resize(frame, (640, height), interpolation=cv2.INTER_AREA)
        return resized, scale

    def _restore_size(self, frame: BGRImage, original: BGRImage, scale: float) -> BGRImage:
        if scale == 1.0:
            return frame
        import cv2

        size = (original.shape[1], original.shape[0])
        return cv2.resize(frame, size, interpolation=cv2.INTER_LINEAR)
