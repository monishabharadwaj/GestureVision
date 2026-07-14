from __future__ import annotations

"""Tests for X sign gesture and paint ink cycling."""

import numpy as np

from gesturevision.core.types import GestureType, HandResult
from gesturevision.effects.interactive.brush_renderers import BRUSH_COLOR_PRESETS
from gesturevision.effects.interactive.virtual_brush import VirtualBrushEffect
from gesturevision.gesture_recognition.gestures.peace import PeaceRule
from gesturevision.gesture_recognition.gestures.x_sign import XSignRule
from gesturevision.hand_tracking import landmarks as lm


def _hand_with_tip_gap(gap: float) -> HandResult:
    points = np.zeros((21, 3), dtype=np.float32)
    for tip, pip in (
        (lm.INDEX_TIP, lm.INDEX_PIP),
        (lm.MIDDLE_TIP, lm.MIDDLE_PIP),
    ):
        points[pip] = (0.5, 0.6, 0.0)
        points[tip] = (0.5, 0.4, 0.0)
    points[lm.INDEX_TIP][0] = 0.5 - gap / 2
    points[lm.MIDDLE_TIP][0] = 0.5 + gap / 2
    for tip, pip in ((lm.RING_TIP, lm.RING_PIP), (lm.PINKY_TIP, lm.PINKY_PIP)):
        points[pip] = (0.5, 0.55, 0.0)
        points[tip] = (0.5, 0.65, 0.0)
    return HandResult(landmarks=points, handedness="Right", confidence=0.95)


def test_x_sign_detects_crossed_fingers() -> None:
    rule = XSignRule()
    assert rule.evaluate(_hand_with_tip_gap(0.03)) > 0.5


def test_peace_requires_wide_finger_separation() -> None:
    peace = PeaceRule()
    x_rule = XSignRule()
    crossed = _hand_with_tip_gap(0.03)
    wide = _hand_with_tip_gap(0.14)
    assert x_rule.evaluate(crossed) > peace.evaluate(crossed)
    assert peace.evaluate(wide) > 0.5
    assert x_rule.evaluate(wide) == 0.0


def test_virtual_brush_cycles_ink_colors() -> None:
    effect = VirtualBrushEffect()
    first_name, first_color = effect.cycle_ink_color()
    second_name, second_color = effect.cycle_ink_color()
    assert first_name in BRUSH_COLOR_PRESETS
    assert second_name in BRUSH_COLOR_PRESETS
    assert first_color != second_color or len(BRUSH_COLOR_PRESETS) == 1


def test_virtual_brush_cycles_backgrounds() -> None:
    effect = VirtualBrushEffect()
    assert effect.cycle_background_filter() == "sketch"
    assert effect.cycle_background_filter() == "edge"
    assert effect.cycle_background_filter() == "original"
