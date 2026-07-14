from __future__ import annotations

"""Applies the active effect to each frame."""

import logging
import threading
import time
from typing import Any

from gesturevision.core.types import BGRImage, EffectContext, GestureType, QualityTier
from gesturevision.effects.base import BaseEffect
from gesturevision.effects.interactive.base import InteractiveEffect
from gesturevision.effects.registry import build_effects_from_config

logger = logging.getLogger(__name__)


class EffectEngine:
    """Thread-safe effect processor with runtime parameter control."""

    def __init__(self, config: dict[str, Any]) -> None:
        effects_cfg = config.get("effects", config)
        self._effects = build_effects_from_config(config)
        self._active = str(effects_cfg.get("default", "original")).lower()
        self._quality: QualityTier = effects_cfg.get("quality_tier", "preview")
        if self._active not in self._effects:
            self._active = "original"
        self._lock = threading.Lock()
        self._last_apply_ms = 0.0

    @property
    def active_effect(self) -> str:
        with self._lock:
            return self._active

    @property
    def quality(self) -> QualityTier:
        with self._lock:
            return self._quality

    @property
    def available_effects(self) -> list[str]:
        return sorted(self._effects.keys())

    @property
    def last_apply_ms(self) -> float:
        return self._last_apply_ms

    def set_active_effect(self, name: str) -> bool:
        normalized = name.strip().lower()
        with self._lock:
            if normalized not in self._effects:
                logger.warning("Attempted to activate unknown effect: %s", normalized)
                return False

            previous = self._effects.get(self._active)
            if isinstance(previous, InteractiveEffect):
                previous.reset()

            if normalized != self._active:
                logger.info("Active effect: %s → %s", self._active, normalized)
            self._active = normalized
            return True

    def reset_active_effect(self) -> None:
        """Clear state on the currently active interactive effect."""
        with self._lock:
            effect = self._effects.get(self._active)
            if isinstance(effect, InteractiveEffect):
                effect.reset()

    def set_quality(self, quality: QualityTier) -> None:
        with self._lock:
            self._quality = quality

    def adjust_active_parameter(self, key: str, normalized_value: float) -> None:
        """
        Map a normalized value in [0, 1] to an effect parameter.

        Supports blur strength, brush radius, and reveal radius.
        """
        with self._lock:
            effect = self._effects.get(self._active)
            if effect is None:
                return

            if self._active == "blur" and key in {"strength", "active.strength"}:
                min_strength = int(effect.params.get("min_strength", 3))
                max_strength = int(effect.params.get("max_strength", 31))
                strength = int(min_strength + normalized_value * (max_strength - min_strength))
                if strength % 2 == 0:
                    strength += 1
                effect.set_param("strength", strength)
            elif self._active == "brush" and key in {"strength", "radius", "active.strength"}:
                min_radius = int(effect.params.get("min_radius", 8))
                max_radius = int(effect.params.get("max_radius", 48))
                radius = int(min_radius + normalized_value * (max_radius - min_radius))
                effect.set_param("brush_radius", radius)
            elif self._active == "reveal" and key in {"strength", "radius", "active.strength"}:
                min_feather = int(effect.params.get("min_feather", 16))
                max_feather = int(effect.params.get("max_feather", 140))
                feather = int(min_feather + normalized_value * (max_feather - min_feather))
                effect.set_param("feather_width", feather)

    def set_brush_type(self, brush_type: str) -> None:
        from gesturevision.effects.interactive.virtual_brush import VirtualBrushEffect

        brush = self._effects.get("brush")
        if isinstance(brush, VirtualBrushEffect):
            brush.set_brush_type(brush_type)

    def set_brush_color(self, bgr: tuple[int, int, int]) -> None:
        from gesturevision.effects.interactive.virtual_brush import VirtualBrushEffect

        brush = self._effects.get("brush")
        if isinstance(brush, VirtualBrushEffect):
            brush.set_color(bgr)

    def set_reveal_overlay(self, effect_name: str) -> None:
        from gesturevision.effects.interactive.image_reveal import ImageRevealEffect

        reveal = self._effects.get("reveal")
        if isinstance(reveal, ImageRevealEffect):
            reveal.set_overlay_effect(effect_name)

    def get_effect(self, name: str) -> BaseEffect | None:
        return self._effects.get(name.strip().lower())

    def apply(
        self,
        frame: BGRImage,
        *,
        finger_position: tuple[float, float] | None = None,
        pixel_position: tuple[int, int] | None = None,
        active_gesture: GestureType = GestureType.UNKNOWN,
        pinch_strength: float = 0.0,
        extra_params: dict[str, Any] | None = None,
    ) -> BGRImage:
        """Apply the active effect and return the processed frame."""
        start = time.perf_counter()
        drawing = active_gesture == GestureType.INDEX_FINGER

        with self._lock:
            active = self._active
            effect = self._effects[active]
            quality = self._quality
            params = dict(effect.params)

        if extra_params:
            params.update(extra_params)

        ctx = EffectContext(
            frame=frame,
            finger_position=finger_position,
            pixel_position=pixel_position,
            active_gesture=active_gesture,
            drawing=drawing,
            pinch_strength=pinch_strength,
            params=params,
            quality=quality,
        )
        result = effect.apply(ctx)
        self._last_apply_ms = (time.perf_counter() - start) * 1000.0
        return result
