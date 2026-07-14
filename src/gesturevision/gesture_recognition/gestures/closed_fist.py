from __future__ import annotations

from gesturevision.core.types import GestureType, HandResult
from gesturevision.gesture_recognition.finger_geometry import all_fingers_curled, thumb_extended


class ClosedFistRule:
    gesture = GestureType.CLOSED_FIST

    def evaluate(self, hand: HandResult) -> float:
        points = hand.landmarks
        if not all_fingers_curled(points):
            return 0.0
        if thumb_extended(points):
            return 0.0
        return 0.88 * hand.confidence


rule = ClosedFistRule()
