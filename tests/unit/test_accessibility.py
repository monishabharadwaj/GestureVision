from __future__ import annotations

"""Unit tests for speech, voice parsing, and touch navigation."""

from gesturevision.accessibility.speech_utils import matches_beauty_trigger
from gesturevision.accessibility.touch_navigation import TouchNavigator, zones_from_app_ids
from gesturevision.accessibility.voice_parser import build_phrase_map, match_spoken_command


def test_beauty_fuzzy_match() -> None:
    assert matches_beauty_trigger("beauty", ["beauty"])
    assert matches_beauty_trigger("I am beauty please", ["beauty"])
    assert matches_beauty_trigger("booty", ["beauty"])
    assert not matches_beauty_trigger("dandelion", ["beauty"])


def test_natural_speech_open_youtube() -> None:
    phrases = build_phrase_map(
        {"youtube": ["open youtube"], "chrome": ["open chrome"]},
        {"youtube": {"label": "YouTube"}, "chrome": {"label": "Chrome"}},
    )
    assert match_spoken_command("please open youtube now", phrases) == "youtube"
    assert match_spoken_command("open chrome browser", phrases) == "chrome"


def test_touch_navigator_tap_on_pinch() -> None:
    zones = zones_from_app_ids(
        ["chrome", "youtube"],
        {"chrome": {"label": "Chrome"}, "youtube": {"label": "YouTube"}},
    )
    nav = TouchNavigator(zones=zones, dwell_seconds=0.01, tap_cooldown=0.0)
    hover, tap = nav.update(0.75, 0.9, pointing=True, pinching=True)
    assert hover == "youtube"
    assert tap == "youtube"
