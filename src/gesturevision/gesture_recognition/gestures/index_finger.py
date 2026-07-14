from __future__ import annotations

from gesturevision.core.types import GestureType, HandResult
from gesturevision.gesture_recognition.finger_geometry import (
    is_finger_curled,
    is_finger_extended,
)
from gesturevision.gesture_recognition.rules import GestureRule
from gesturevision.hand_tracking import landmarks as lm


class IndexFingerRule:
    gesture = GestureType.INDEX_FINGER

    def evaluate(self, hand: HandResult) -> float:
        points = hand.landmarks
        if not is_finger_extended(points, lm.INDEX_TIP, lm.INDEX_PIP):
            return 0.0
        if not all(
            is_finger_curled(points, tip, pip)
            for tip, pip in (
                (lm.MIDDLE_TIP, lm.MIDDLE_PIP),
                (lm.RING_TIP, lm.RING_PIP),
                (lm.PINKY_TIP, lm.PINKY_PIP),
            )
        ):
            return 0.0
        return 0.9 * hand.confidence


rule = IndexFingerRule()
