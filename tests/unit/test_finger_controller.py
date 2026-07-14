from __future__ import annotations

"""Unit tests for finger controller."""

import numpy as np
import pytest

from gesturevision.hand_tracking import landmarks as lm
from gesturevision.input.finger_controller import FingerController


def _make_hand(*, index_y: float = 0.3, handedness: str = "Right"):
    landmarks = np.zeros((21, 3), dtype=np.float32)
    landmarks[lm.INDEX_TIP] = (0.5, index_y, 0.0)
    from gesturevision.core.types import HandResult

    return HandResult(landmarks=landmarks, handedness=handedness, confidence=0.95)


def test_finger_controller_tracks_dominant_hand() -> None:
    controller = FingerController(dominant_hand="Right", mirror=False)
    hand = _make_hand()
    position = controller.update([hand])

    assert position[0] == 0.5
    assert position[1] == pytest.approx(0.3)
