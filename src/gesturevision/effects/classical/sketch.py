from __future__ import annotations

"""Pencil sketch effect using dodge blending."""

import cv2
import numpy as np

from gesturevision.core.types import BGRImage, EffectContext
from gesturevision.effects.base import BaseEffect


class SketchEffect(BaseEffect):
    name = "sketch"
    default_params = {"blur_ksize": 21}

    def apply(self, ctx: EffectContext) -> BGRImage:
        source, scale = self._processing_frame(ctx)
        params = self._merged_params(ctx)
        ksize = int(params.get("blur_ksize", 21))
        if ksize % 2 == 0:
            ksize += 1

        gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
        inverted = 255 - gray
        blurred = cv2.GaussianBlur(inverted, (ksize, ksize), 0)
        denom = np.clip(255 - blurred, 1, 255).astype(np.float32)
        sketch = np.clip((gray.astype(np.float32) * 256.0) / denom, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(sketch, cv2.COLOR_GRAY2BGR)
        return self._restore_size(result, ctx.frame, scale)


effect = SketchEffect
