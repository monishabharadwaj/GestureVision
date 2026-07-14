from __future__ import annotations

from gesturevision.core.types import GestureType, HandResult
from gesturevision.gesture_recognition.finger_geometry import fingertip_distance, pinch_strength
from gesturevision.hand_tracking import landmarks as lm


class PinchRule:
    gesture = GestureType.PINCH
    _max_distance = 0.08

    def evaluate(self, hand: HandResult) -> float:
        points = hand.landmarks
        distance = fingertip_distance(points, lm.THUMB_TIP, lm.INDEX_TIP)
        if distance > self._max_distance:
            return 0.0
        strength = pinch_strength(points)
        return max(0.5, strength) * hand.confidence


rule = PinchRule()
