from __future__ import annotations

"""Unit tests for gesture debouncer."""

import time

from gesturevision.core.types import GestureType
from gesturevision.gesture_recognition.debouncer import GestureDebouncer


def test_debouncer_fires_one_shot_action_once() -> None:
    debouncer = GestureDebouncer(
        default_frames=3,
        per_gesture_frames={GestureType.PEACE: 3},
    )
    ts = time.perf_counter()

    for _ in range(2):
        result = debouncer.update(
            GestureType.PEACE,
            hand="Right",
            confidence=0.9,
            timestamp=ts,
        )
        assert result.action_event is None

    result = debouncer.update(
        GestureType.PEACE,
        hand="Right",
        confidence=0.9,
        timestamp=ts,
    )
    assert result.action_event is not None
    assert result.action_event.gesture == GestureType.PEACE

    result = debouncer.update(
        GestureType.PEACE,
        hand="Right",
        confidence=0.9,
        timestamp=ts,
    )
    assert result.action_event is None


def test_debouncer_resets_on_unknown() -> None:
    debouncer = GestureDebouncer(default_frames=1)
    debouncer.update(GestureType.PEACE, hand="Right", confidence=0.9, timestamp=0.0)
    result = debouncer.update(GestureType.UNKNOWN, hand="Right", confidence=0.0, timestamp=0.1)
    assert result.display_gesture == GestureType.UNKNOWN


def test_pinch_fires_when_debounced_for_discrete_actions() -> None:
    debouncer = GestureDebouncer(
        per_gesture_frames={GestureType.PINCH: 3},
    )
    for _ in range(2):
        result = debouncer.update(
            GestureType.PINCH,
            hand="Right",
            confidence=0.9,
            timestamp=0.0,
        )
        assert result.action_event is None

    result = debouncer.update(
        GestureType.PINCH,
        hand="Right",
        confidence=0.9,
        timestamp=0.0,
    )
    assert result.action_event is not None
    assert result.action_event.gesture == GestureType.PINCH


def test_pinch_stays_continuous_when_debounce_zero() -> None:
    debouncer = GestureDebouncer(
        per_gesture_frames={GestureType.PINCH: 0},
    )
    for _ in range(5):
        result = debouncer.update(
            GestureType.PINCH,
            hand="Right",
            confidence=0.9,
            timestamp=0.0,
        )
        assert result.action_event is None
