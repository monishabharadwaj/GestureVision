from __future__ import annotations

"""Canny edge detection effect."""

import cv2

from gesturevision.core.types import BGRImage, EffectContext
from gesturevision.effects.base import BaseEffect


class EdgeEffect(BaseEffect):
    name = "edge"
    default_params = {"low_threshold": 50, "high_threshold": 150, "blur_ksize": 5}

    def apply(self, ctx: EffectContext) -> BGRImage:
        source, scale = self._processing_frame(ctx)
        params = self._merged_params(ctx)
        ksize = int(params.get("blur_ksize", 5))
        if ksize % 2 == 0:
            ksize += 1

        gray = cv2.cvtColor(source, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (ksize, ksize), 0)
        edges = cv2.Canny(
            blurred,
            int(params.get("low_threshold", 50)),
            int(params.get("high_threshold", 150)),
        )
        result = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        return self._restore_size(result, ctx.frame, scale)


effect = EdgeEffect
