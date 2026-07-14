from __future__ import annotations

from gesturevision.core.types import GestureType, HandResult
from gesturevision.gesture_recognition.finger_geometry import (
    fingertip_distance,
    is_finger_extended,
)
from gesturevision.hand_tracking import landmarks as lm


class OkSignRule:
    gesture = GestureType.OK_SIGN
    _max_circle_distance = 0.06

    def evaluate(self, hand: HandResult) -> float:
        points = hand.landmarks
        circle_dist = fingertip_distance(points, lm.THUMB_TIP, lm.INDEX_TIP)
        if circle_dist > self._max_circle_distance:
            return 0.0
        if not all(
            is_finger_extended(points, tip, pip)
            for tip, pip in (
                (lm.MIDDLE_TIP, lm.MIDDLE_PIP),
                (lm.RING_TIP, lm.RING_PIP),
                (lm.PINKY_TIP, lm.PINKY_PIP),
            )
        ):
            return 0.0
        return 0.93 * hand.confidence


rule = OkSignRule()
