from __future__ import annotations

"""Passthrough effect — returns the original frame."""

from gesturevision.core.types import BGRImage, EffectContext
from gesturevision.effects.base import BaseEffect


class OriginalEffect(BaseEffect):
    name = "original"
    default_params: dict = {}

    def apply(self, ctx: EffectContext) -> BGRImage:
        return ctx.frame.copy()


effect = OriginalEffect
