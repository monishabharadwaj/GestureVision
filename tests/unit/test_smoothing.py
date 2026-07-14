from __future__ import annotations

"""Unit tests for landmark smoothing."""

import numpy as np

from gesturevision.core.types import HandResult
from gesturevision.hand_tracking.smoothing import LandmarkSmoother


def _hand(x: float) -> HandResult:
    landmarks = np.zeros((21, 3), dtype=np.float32)
    landmarks[8] = (x, 0.5, 0.0)
    return HandResult(landmarks=landmarks, handedness="Right", confidence=0.9)


def test_smoother_interpolates_positions() -> None:
    smoother = LandmarkSmoother(alpha=0.5)
    first = smoother.smooth([_hand(0.2)])
    second = smoother.smooth([_hand(0.8)])

    assert first[0].landmarks[8][0] == 0.2
    assert second[0].landmarks[8][0] == 0.5


def test_smoother_clears_lost_hands() -> None:
    smoother = LandmarkSmoother(alpha=0.5)
    smoother.smooth([_hand(0.3)])
    assert "Right" in smoother._state
    smoother.smooth([])
    assert "Right" not in smoother._state
