from __future__ import annotations

from gesturevision.core.types import GestureType, HandResult
from gesturevision.gesture_recognition.finger_geometry import (
    fingertip_distance,
    is_finger_curled,
    is_finger_extended,
)
from gesturevision.hand_tracking import landmarks as lm


class XSignRule:
    """Index and middle fingers crossed — means done / cancel / exit paint."""

    gesture = GestureType.X_SIGN

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
        # Crossed fingers — tips close together (peace/V has wide separation).
        if fingertip_distance(points, lm.INDEX_TIP, lm.MIDDLE_TIP) > 0.055:
            return 0.0
        return 0.94 * hand.confidence


rule = XSignRule()
