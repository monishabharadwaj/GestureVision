from __future__ import annotations

from gesturevision.core.types import GestureType, HandResult
from gesturevision.gesture_recognition.finger_geometry import thumb_up_pose


class ThumbsUpRule:
    gesture = GestureType.THUMBS_UP

    def evaluate(self, hand: HandResult) -> float:
        if not thumb_up_pose(hand.landmarks):
            return 0.0
        return 0.9 * hand.confidence


rule = ThumbsUpRule()
