from __future__ import annotations

"""Dandelion gesture mode separation tests."""

from gesturevision.accessibility.profile_config import load_profile_settings
from gesturevision.core.types import AccessibilityProfile
from gesturevision.gesture_recognition.actions import ActionType
from gesturevision.gesture_recognition.gesture_router import GestureRouter


def _router_with_dandelion() -> GestureRouter:
    from gesturevision.accessibility.profile_config import load_profile_settings

    settings = load_profile_settings(
        {
            "accessibility": {
                "profiles": {
                    "dandelion": {
                        "gestures": {
                            "rock_sign": {"action": "start_music_chat", "debounce_frames": 8},
                            "peace": {"action": "start_learn_chat", "debounce_frames": 8},
                            "ok_sign": {"action": "start_free_chat", "debounce_frames": 8},
                            "thumbs_up": {"action": "enter_paint_mode", "debounce_frames": 8},
                            "closed_fist": {"action": "exit_paint_mode", "debounce_frames": 8},
                        },
                        "paint_gestures": {
                            "peace": "movie sketch",
                            "rock_sign": "movie edge",
                        },
                    }
                }
            }
        },
        AccessibilityProfile.DANDELION,
    )
    router = GestureRouter({"gestures": {"mappings": {}}})
    router.apply_profile_mappings(settings.gesture_mappings)
    return router


def test_dandelion_live_gestures_are_separate() -> None:
    import time

    from gesturevision.core.types import GestureEvent, GestureType

    router = _router_with_dandelion()
    ts = time.perf_counter()

    music = router.route(
        GestureEvent(gesture=GestureType.ROCK_SIGN, hand="Right", confidence=0.9, timestamp=ts)
    )
    learn = router.route(
        GestureEvent(gesture=GestureType.PEACE, hand="Right", confidence=0.9, timestamp=ts)
    )
    paint = router.route(
        GestureEvent(gesture=GestureType.THUMBS_UP, hand="Right", confidence=0.9, timestamp=ts)
    )

    assert music is not None and music.action == ActionType.START_MUSIC_CHAT
    assert learn is not None and learn.action == ActionType.START_LEARN_CHAT
    assert paint is not None and paint.action == ActionType.ENTER_PAINT_MODE


def test_dandelion_profile_loads_paint_hints() -> None:
    settings = load_profile_settings(
        {
            "accessibility": {
                "profiles": {
                    "dandelion": {
                        "paint_gestures": {
                            "peace": "movie sketch background",
                            "rock_sign": "movie edge background",
                        }
                    }
                }
            }
        },
        AccessibilityProfile.DANDELION,
    )
    assert settings.paint_gesture_hints["peace"] == "movie sketch background"
