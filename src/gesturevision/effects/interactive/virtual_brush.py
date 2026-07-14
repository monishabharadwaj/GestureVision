from __future__ import annotations

"""Multi-style neon and 3D finger painting."""

import cv2
import numpy as np

from gesturevision.core.types import BGRImage, EffectContext
from gesturevision.effects.interactive.base import InteractiveEffect
from gesturevision.effects.interactive.brush_renderers import (
    BRUSH_TYPES,
    finalize_glow,
)


class VirtualBrushEffect(InteractiveEffect):
    """Paint with selectable brush styles and custom colors."""

    name = "brush"
    default_params = {
        "brush_type": "neon",
        "brush_radius": 16,
        "min_radius": 8,
        "max_radius": 40,
        "neon_color": (255, 80, 255),
        "core_color": (255, 220, 255),
        "glow_blur": 21,
        "glow_intensity": 1.35,
        "depth_offset": 4,
    }

    def __init__(
        self,
        params: dict | None = None,
        processors: dict | None = None,
    ) -> None:
        super().__init__(params)
        self._processors = processors or {}
        self._glow_layer: np.ndarray | None = None
        self._last_pixel: tuple[int, int] | None = None

    def reset(self) -> None:
        self._glow_layer = None
        self._last_pixel = None

    def set_brush_type(self, brush_type: str) -> None:
        if brush_type in BRUSH_TYPES:
            self.set_param("brush_type", brush_type)

    def set_color(self, bgr: tuple[int, int, int]) -> None:
        self.set_param("neon_color", bgr)
        self.set_param("core_color", tuple(min(255, int(c * 1.15)) for c in bgr))

    def apply(self, ctx: EffectContext) -> BGRImage:
        frame = ctx.frame
        height, width = frame.shape[:2]
        params = self._merged_params(ctx)
        radius = int(params.get("brush_radius", 16))

        if self._glow_layer is None or self._glow_layer.shape != (height, width, 3):
            self._glow_layer = np.zeros((height, width, 3), dtype=np.float32)
            self._last_pixel = None

        brush_type = str(params.get("brush_type", "neon"))
        renderer = BRUSH_TYPES.get(brush_type, BRUSH_TYPES["neon"])
        neon = tuple(params.get("neon_color", (255, 80, 255)))
        core = tuple(params.get("core_color", (255, 220, 255)))

        if ctx.drawing and ctx.pixel_position is not None:
            renderer(
                self._glow_layer,
                ctx.pixel_position,
                radius,
                neon,
                core,
                self._last_pixel,
                depth_offset=int(params.get("depth_offset", 4)),
            )
            self._last_pixel = ctx.pixel_position
        else:
            self._last_pixel = None

        glow = finalize_glow(
            self._glow_layer,
            int(params.get("glow_blur", 21)),
            float(params.get("glow_intensity", 1.35)),
        )
        result = frame.astype(np.float32) + glow
        return np.clip(result, 0, 255).astype(np.uint8)


effect = VirtualBrushEffect
