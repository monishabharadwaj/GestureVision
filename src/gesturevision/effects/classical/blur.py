from __future__ import annotations

"""Gaussian blur with configurable strength."""

import cv2

from gesturevision.core.types import BGRImage, EffectContext
from gesturevision.effects.base import BaseEffect


class BlurEffect(BaseEffect):
    name = "blur"
    default_params = {"strength": 7, "min_strength": 3, "max_strength": 31}

    def apply(self, ctx: EffectContext) -> BGRImage:
        params = self._merged_params(ctx)
        strength = int(params.get("strength", 7))
        min_strength = int(params.get("min_strength", 3))
        max_strength = int(params.get("max_strength", 31))
        strength = max(min_strength, min(max_strength, strength))
        if strength % 2 == 0:
            strength += 1
        return cv2.GaussianBlur(ctx.frame, (strength, strength), 0)


effect = BlurEffect
