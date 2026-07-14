from __future__ import annotations

"""Unit tests for gesture router."""

import time

from gesturevision.core.types import GestureEvent, GestureType
from gesturevision.gesture_recognition.actions import ActionType
from gesturevision.gesture_recognition.gesture_router import GestureRouter


def _config() -> dict:
    return {
        "gestures": {
            "mappings": {
                "peace": {"action": "switch_effect", "target": "sketch", "debounce_frames": 5},
                "pinch": {"action": "adjust_parameter", "target": "active.strength", "debounce_frames": 0},
                "thumbs_up": {"action": "capture_screenshot", "debounce_frames": 10},
            }
        }
    }


def test_router_maps_switch_effect() -> None:
    router = GestureRouter(_config())
    event = GestureEvent(
        gesture=GestureType.PEACE,
        hand="Right",
        confidence=0.9,
        timestamp=time.perf_counter(),
    )
    command = router.route(event)
    assert command is not None
    assert command.action == ActionType.SWITCH_EFFECT
    assert command.target == "sketch"


def test_router_maps_continuous_pinch() -> None:
    router = GestureRouter(_config())
    command = router.route_continuous(GestureType.PINCH, "Right", pinch_strength=0.75)
    assert command is not None
    assert command.action == ActionType.ADJUST_PARAMETER
    assert command.value == 0.75
