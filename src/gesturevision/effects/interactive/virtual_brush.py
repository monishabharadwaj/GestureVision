from __future__ import annotations

"""Multi-style neon and 3D finger painting with movie backgrounds and stickers."""

import cv2
import numpy as np

from gesturevision.core.types import BGRImage, EffectContext
from gesturevision.effects.interactive.base import InteractiveEffect
from gesturevision.effects.interactive.brush_renderers import (
    BRUSH_TYPES,
    finalize_glow,
)
from gesturevision.effects.interactive.paint_stickers import STICKER_CYCLE, STICKER_RENDERERS


class VirtualBrushEffect(InteractiveEffect):
    """Paint on live camera with optional movie filters and 3D stickers."""

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
        "background_filter": "original",
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
        self._stickers: list[dict[str, object]] = []
        self._next_sticker = 0

    def reset(self) -> None:
        self._glow_layer = None
        self._last_pixel = None
        self._stickers.clear()
        self._next_sticker = 0

    def set_brush_type(self, brush_type: str) -> None:
        if brush_type in BRUSH_TYPES:
            self.set_param("brush_type", brush_type)

    def set_color(self, bgr: tuple[int, int, int]) -> None:
        self.set_param("neon_color", bgr)
        self.set_param("core_color", tuple(min(255, int(c * 1.15)) for c in bgr))

    def set_background_filter(self, filter_name: str) -> None:
        normalized = filter_name.strip().lower()
        if normalized in {"original", "sketch", "edge", "blur"}:
            self.set_param("background_filter", normalized)

    def cycle_brush_type(self) -> str:
        order = ("neon", "tube3d", "sparkle", "soft")
        current = str(self.params.get("brush_type", "neon"))
        try:
            index = order.index(current)
        except ValueError:
            index = -1
        next_type = order[(index + 1) % len(order)]
        self.set_brush_type(next_type)
        return next_type

    def place_sticker(self, position: tuple[int, int] | None) -> str:
        if position is None:
            return ""
        sticker_type = STICKER_CYCLE[self._next_sticker % len(STICKER_CYCLE)]
        self._next_sticker += 1
        color = tuple(self.params.get("neon_color", (255, 80, 255)))
        self._stickers.append(
            {
                "type": sticker_type,
                "position": position,
                "radius": max(18, int(self.params.get("brush_radius", 16)) + 8),
                "color": color,
            }
        )
        return sticker_type

    def apply(self, ctx: EffectContext) -> BGRImage:
        frame = self._filtered_frame(ctx.frame, self._merged_params(ctx))
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
        painted = np.clip(result, 0, 255).astype(np.uint8)
        self._draw_stickers(painted)
        return painted

    def _filtered_frame(self, frame: BGRImage, params: dict) -> BGRImage:
        filter_name = str(params.get("background_filter", "original")).lower()
        if filter_name == "original":
            return frame
        processor = self._processors.get(filter_name)
        if processor is None:
            return frame
        filtered_ctx = EffectContext(
            frame=frame,
            finger_position=None,
            pixel_position=None,
            active_gesture=params.get("active_gesture"),
            drawing=False,
            pinch_strength=0.0,
            params=dict(processor.params),
            quality="preview",
        )
        return processor.apply(filtered_ctx)

    def _draw_stickers(self, image: BGRImage) -> None:
        for sticker in self._stickers:
            sticker_type = str(sticker["type"])
            renderer = STICKER_RENDERERS.get(sticker_type)
            if renderer is None:
                continue
            position = sticker["position"]
            radius = int(sticker["radius"])
            color = tuple(sticker["color"])  # type: ignore[arg-type]
            if sticker_type == "cube":
                renderer(image, position, radius * 2, color)
            else:
                renderer(image, position, radius, color)


effect = VirtualBrushEffect
