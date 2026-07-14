from __future__ import annotations

"""
Unified reveal / compare mode.

The full frame shows a cinematic filtered look. Moving your finger horizontally
wipes away the filter to reveal the real camera feed — like pulling back a
movie effect to show what's actually there.
"""

import cv2
import numpy as np

from gesturevision.core.types import BGRImage, EffectContext, GestureType
from gesturevision.effects.compositor import apply_processor
from gesturevision.effects.interactive.base import InteractiveEffect


class ImageRevealEffect(InteractiveEffect):
    """Wipe between a cinematic filter and the original live camera."""

    name = "reveal"
    default_params = {
        "overlay_effect": "sketch",
        "cinematic_tint": (50, 25, 90),
        "vignette_strength": 0.45,
        "split_position": 0.5,
        "feather_width": 48,
        "min_feather": 16,
        "max_feather": 140,
    }

    def __init__(
        self,
        params: dict | None = None,
        processors: dict | None = None,
    ) -> None:
        super().__init__(params)
        self._processors = processors or {}
        self.last_split_x = 0
        self.last_feather = 48

    def set_overlay_effect(self, effect_name: str) -> None:
        self.set_param("overlay_effect", effect_name.strip().lower())

    def _cinematic_grade(self, frame: BGRImage, params: dict) -> BGRImage:
        tint = np.array(params.get("cinematic_tint", (50, 25, 90)), dtype=np.float32)
        graded = frame.astype(np.float32)
        graded = graded * 0.75 + tint * 0.35

        strength = float(params.get("vignette_strength", 0.45))
        if strength > 0:
            h, w = frame.shape[:2]
            y, x = np.ogrid[:h, :w]
            cx, cy = w / 2.0, h / 2.0
            dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2)
            max_dist = np.sqrt(cx**2 + cy**2)
            vignette = 1.0 - strength * (dist / max_dist)
            vignette = np.clip(vignette, 0.4, 1.0)[..., None]
            graded *= vignette

        return np.clip(graded, 0, 255).astype(np.uint8)

    def _resolve_feather(self, ctx: EffectContext, params: dict) -> int:
        min_f = int(params.get("min_feather", 16))
        max_f = int(params.get("max_feather", 140))
        base = int(params.get("feather_width", 48))
        if ctx.active_gesture == GestureType.PINCH and ctx.pinch_strength > 0.0:
            return int(min_f + ctx.pinch_strength * (max_f - min_f))
        return base

    def apply(self, ctx: EffectContext) -> BGRImage:
        frame = ctx.frame
        height, width = frame.shape[:2]
        params = self._merged_params(ctx)

        overlay_name = str(params.get("overlay_effect", "sketch"))
        filtered = apply_processor(self._processors, overlay_name, frame, quality=ctx.quality)
        filtered = self._cinematic_grade(filtered, params)

        if ctx.finger_position is not None:
            split_norm = float(np.clip(ctx.finger_position[0], 0.0, 1.0))
        elif ctx.pixel_position is not None:
            split_norm = float(np.clip(ctx.pixel_position[0] / max(width - 1, 1), 0.0, 1.0))
        else:
            split_norm = float(params.get("split_position", 0.5))

        split_x = int(split_norm * width)
        feather = self._resolve_feather(ctx, params)
        self.last_split_x = split_x
        self.last_feather = feather

        mask = np.zeros((height, width), dtype=np.float32)
        x_coords = np.arange(width, dtype=np.float32)
        # Left of the finger = original (revealed reality), right = cinematic filter.
        ramp = (split_x + feather / 2.0 - x_coords) / max(feather, 1.0)
        mask[:, :] = np.clip(ramp, 0.0, 1.0)

        mask3 = mask[..., None]
        original = frame.astype(np.float32)
        cinematic = filtered.astype(np.float32)
        blended = original * mask3 + cinematic * (1.0 - mask3)
        return np.clip(blended, 0, 255).astype(np.uint8)


effect = ImageRevealEffect
