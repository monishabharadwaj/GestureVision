from __future__ import annotations

"""Unit tests for dual-hand 3D mesh AR rendering."""

import numpy as np

from gesturevision.core.types import EffectContext, HandResult
from gesturevision.effects.classical.original import OriginalEffect
from gesturevision.effects.interactive.hand_mesh import HandMeshEffect
from gesturevision.effects.interactive.hand_mesh_renderer import draw_dual_hand_mesh
from gesturevision.hand_tracking import landmarks as lm


def _blank_frame() -> np.ndarray:
    return np.zeros((120, 160, 3), dtype=np.uint8)


def _flat_hand(x_offset: float = 0.3) -> HandResult:
    landmarks = np.zeros((21, 3), dtype=np.float32)
    for index in range(21):
        landmarks[index] = (x_offset, 0.5, 0.0)
    for tip in lm.FINGER_TIPS:
        landmarks[tip] = (x_offset, 0.35, -0.02)
    landmarks[lm.WRIST] = (x_offset, 0.7, 0.0)
    return HandResult(landmarks=landmarks, handedness="Left", confidence=0.9)


def test_dual_hand_mesh_draws_cross_bridges() -> None:
    frame = _blank_frame()
    left = _flat_hand(0.25)
    right = _flat_hand(0.75)
    right = HandResult(landmarks=right.landmarks.copy(), handedness="Right", confidence=0.9)

    before = int(frame.sum())
    draw_dual_hand_mesh(frame, [left, right])
    after = int(frame.sum())
    assert after > before


def test_single_hand_mesh_draws_wireframe() -> None:
    frame = _blank_frame()
    draw_dual_hand_mesh(frame, [_flat_hand(0.5)])
    assert int(frame.sum()) > 0


def test_dual_hand_lattice_is_denser_than_tip_lines_only() -> None:
    frame = _blank_frame()
    left = _flat_hand(0.2)
    right = HandResult(landmarks=_flat_hand(0.8).landmarks.copy(), handedness="Right", confidence=0.9)
    # Spread tip landmarks vertically so slice links are visible.
    for tip, y in zip(lm.FINGER_TIPS, (0.25, 0.30, 0.35, 0.40, 0.45), strict=True):
        left.landmarks[tip] = (0.2, y, -0.02)
        right.landmarks[tip] = (0.8, y, -0.02)
    draw_dual_hand_mesh(frame, [left, right])
    # Interior midpoints between hands should be painted by the lattice.
    mid_pixel = frame[36, 80]
    assert int(mid_pixel.sum()) > 0


def test_hand_mesh_effect_uses_hands_context() -> None:
    processors = {"original": OriginalEffect()}
    effect = HandMeshEffect(processors=processors)
    frame = _blank_frame()
    result = effect.apply(
        EffectContext(
            frame=frame,
            hands=[_flat_hand(0.3), _flat_hand(0.7)],
        )
    )
    assert not np.array_equal(result, frame)
