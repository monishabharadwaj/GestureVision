from __future__ import annotations

"""Helpers for composing classical effects inside interactive modes."""

from typing import Any

from gesturevision.core.types import BGRImage, EffectContext, QualityTier
from gesturevision.effects.base import BaseEffect


def apply_processor(
    processors: dict[str, BaseEffect],
    name: str,
    frame: BGRImage,
    *,
    quality: QualityTier = "preview",
    params: dict[str, Any] | None = None,
) -> BGRImage:
    """Run a named classical effect on a frame."""
    processor = processors.get(name)
    if processor is None:
        return frame.copy()

    ctx = EffectContext(
        frame=frame,
        params=params or {},
        quality=quality,
    )
    return processor.apply(ctx)
