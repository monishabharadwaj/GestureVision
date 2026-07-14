from __future__ import annotations

"""Unit tests for interactive finger-driven effects."""

import numpy as np

from gesturevision.core.types import EffectContext, GestureType
from gesturevision.effects.classical.edge import EdgeEffect
from gesturevision.effects.classical.original import OriginalEffect
from gesturevision.effects.classical.sketch import SketchEffect
from gesturevision.effects.interactive.image_reveal import ImageRevealEffect
from gesturevision.effects.interactive.virtual_brush import VirtualBrushEffect
from gesturevision.input.finger_controller import FingerController


def _frame() -> np.ndarray:
    frame = np.zeros((100, 160, 3), dtype=np.uint8)
    frame[:, :80] = (30, 30, 200)
    frame[:, 80:] = (30, 200, 30)
    return frame


def _processors() -> dict:
    return {
        "original": OriginalEffect(),
        "sketch": SketchEffect(),
        "edge": EdgeEffect(),
    }


def test_cursor_not_double_mirrored_on_display_frame() -> None:
    controller = FingerController(dominant_hand="Right", mirror=False)
    from gesturevision.core.types import HandResult
    from gesturevision.hand_tracking import landmarks as lm

    landmarks = np.zeros((21, 3), dtype=np.float32)
    landmarks[lm.INDEX_TIP] = (0.8, 0.5, 0.0)
    hand = HandResult(landmarks=landmarks, handedness="Right", confidence=0.9)
    controller.update([hand])
    px, _ = controller.pixel_position(160, 100)
    assert px > 120


def test_virtual_brush_paints_neon() -> None:
    effect = VirtualBrushEffect({"brush_radius": 12, "brush_type": "neon"}, _processors())
    first = effect.apply(
        EffectContext(
            frame=_frame(),
            pixel_position=(60, 50),
            drawing=True,
            active_gesture=GestureType.INDEX_FINGER,
        )
    )
    assert not np.array_equal(first, _frame())


def test_virtual_brush_tube3d_style() -> None:
    effect = VirtualBrushEffect({"brush_type": "tube3d", "brush_radius": 14}, _processors())
    result = effect.apply(
        EffectContext(
            frame=_frame(),
            pixel_position=(80, 50),
            drawing=True,
            active_gesture=GestureType.INDEX_FINGER,
        )
    )
    assert not np.array_equal(result, _frame())


def test_virtual_brush_custom_color() -> None:
    effect = VirtualBrushEffect(processors=_processors())
    effect.set_color((0, 255, 255))
    assert effect.params["neon_color"] == (0, 255, 255)


def test_reveal_shows_original_on_left_of_finger() -> None:
    effect = ImageRevealEffect({"overlay_effect": "sketch", "feather_width": 10}, _processors())
    frame = _frame()
    left_color = frame[50, 20]
    right_color = frame[50, 140]

    result = effect.apply(
        EffectContext(frame=frame, finger_position=(0.5, 0.5))
    )

    assert np.array_equal(result[50, 20], left_color)
    assert not np.array_equal(result[50, 140], right_color)


def test_reveal_pinch_controls_feather() -> None:
    effect = ImageRevealEffect(
        {"min_feather": 16, "max_feather": 140, "feather_width": 48},
        _processors(),
    )
    effect.apply(
        EffectContext(
            frame=_frame(),
            finger_position=(0.5, 0.5),
            active_gesture=GestureType.PINCH,
            pinch_strength=1.0,
        )
    )
    assert effect.last_feather == 140
