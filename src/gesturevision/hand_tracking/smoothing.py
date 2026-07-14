from __future__ import annotations

"""Exponential moving average smoothing for hand landmark stability."""

import numpy as np
from numpy.typing import NDArray

from gesturevision.core.types import HandResult, Handedness


class LandmarkSmoother:
    """Per-hand EMA filter over 21 landmark positions."""

    def __init__(self, alpha: float = 0.4) -> None:
        if not 0.0 < alpha <= 1.0:
            raise ValueError("alpha must be in (0, 1]")
        self._alpha = alpha
        self._state: dict[Handedness, NDArray[np.float32]] = {}

    @property
    def alpha(self) -> float:
        return self._alpha

    def reset(self) -> None:
        """Clear all smoothed state."""
        self._state.clear()

    def smooth(self, hands: list[HandResult]) -> list[HandResult]:
        """Return hands with temporally smoothed landmark positions."""
        smoothed: list[HandResult] = []
        active_hands: set[Handedness] = set()

        for hand in hands:
            active_hands.add(hand.handedness)
            previous = self._state.get(hand.handedness)
            if previous is None:
                filtered = hand.landmarks.astype(np.float32, copy=True)
            else:
                filtered = (
                    self._alpha * hand.landmarks + (1.0 - self._alpha) * previous
                ).astype(np.float32)

            self._state[hand.handedness] = filtered
            smoothed.append(
                HandResult(
                    landmarks=filtered,
                    handedness=hand.handedness,
                    confidence=hand.confidence,
                )
            )

        # Drop stale hands that are no longer tracked.
        for handedness in list(self._state):
            if handedness not in active_hands:
                del self._state[handedness]

        return smoothed
