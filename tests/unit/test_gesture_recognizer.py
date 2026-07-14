from __future__ import annotations

"""Unit tests for gesture rules and recognizer."""

import numpy as np

from gesturevision.core.types import GestureType, HandResult
from gesturevision.gesture_recognition.gestures.index_finger import IndexFingerRule
from gesturevision.gesture_recognition.gestures.peace import PeaceRule
from gesturevision.gesture_recognition.gestures.pinch import PinchRule
from gesturevision.gesture_recognition.recognizer import GestureRecognizer
from gesturevision.hand_tracking import landmarks as lm


def _base_landmarks() -> np.ndarray:
    landmarks = np.zeros((21, 3), dtype=np.float32)
    for tip, pip in (
        (lm.INDEX_TIP, lm.INDEX_PIP),
        (lm.MIDDLE_TIP, lm.MIDDLE_PIP),
        (lm.RING_TIP, lm.RING_PIP),
        (lm.PINKY_TIP, lm.PINKY_PIP),
        (lm.THUMB_TIP, lm.THUMB_IP),
    ):
        landmarks[pip] = (0.5, 0.5, 0.0)
        landmarks[tip] = (0.5, 0.7, 0.0)
    return landmarks


def _hand_from_landmarks(landmarks: np.ndarray) -> HandResult:
    return HandResult(landmarks=landmarks, handedness="Right", confidence=0.95)


def test_index_finger_rule() -> None:
    landmarks = _base_landmarks()
    landmarks[lm.INDEX_TIP] = (0.5, 0.3, 0.0)
    assert IndexFingerRule().evaluate(_hand_from_landmarks(landmarks)) > 0.5


def test_peace_rule() -> None:
    landmarks = _base_landmarks()
    landmarks[lm.INDEX_TIP] = (0.45, 0.3, 0.0)
    landmarks[lm.MIDDLE_TIP] = (0.55, 0.3, 0.0)
    assert PeaceRule().evaluate(_hand_from_landmarks(landmarks)) > 0.5


def test_pinch_rule() -> None:
    landmarks = _base_landmarks()
    landmarks[lm.THUMB_TIP] = (0.48, 0.4, 0.0)
    landmarks[lm.INDEX_TIP] = (0.52, 0.4, 0.0)
    assert PinchRule().evaluate(_hand_from_landmarks(landmarks)) > 0.5


def test_recognizer_selects_peace_over_index() -> None:
    landmarks = _base_landmarks()
    landmarks[lm.INDEX_TIP] = (0.45, 0.3, 0.0)
    landmarks[lm.MIDDLE_TIP] = (0.55, 0.3, 0.0)

    config = {
        "gestures": {
            "min_confidence": 0.5,
            "dominant_hand": "Right",
            "debounce_frames": 1,
            "mappings": {
                "peace": {"action": "switch_effect", "target": "sketch", "debounce_frames": 1},
            },
        }
    }
    recognizer = GestureRecognizer(config)
    result, _ = recognizer.recognize([_hand_from_landmarks(landmarks)])
    assert result.display_gesture == GestureType.PEACE
