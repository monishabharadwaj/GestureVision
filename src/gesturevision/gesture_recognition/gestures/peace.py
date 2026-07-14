from __future__ import annotations

from gesturevision.core.types import GestureType, HandResult
from gesturevision.gesture_recognition.finger_geometry import (
    is_finger_curled,
    is_finger_extended,
)
from gesturevision.hand_tracking import landmarks as lm


class PeaceRule:
    gesture = GestureType.PEACE

    def evaluate(self, hand: HandResult) -> float:
        points = hand.landmarks
        if not is_finger_extended(points, lm.INDEX_TIP, lm.INDEX_PIP):
            return 0.0
        if not is_finger_extended(points, lm.MIDDLE_TIP, lm.MIDDLE_PIP):
            return 0.0
        if not is_finger_curled(points, lm.RING_TIP, lm.RING_PIP):
            return 0.0
        if not is_finger_curled(points, lm.PINKY_TIP, lm.PINKY_PIP):
            return 0.0
        return 0.92 * hand.confidence


rule = PeaceRule()
