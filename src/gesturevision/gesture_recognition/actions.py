from __future__ import annotations

"""Gesture action definitions produced by the router."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from gesturevision.core.types import GestureType, Handedness


class ActionType(str, Enum):
    """Supported gesture-driven actions."""

    TRACK_CURSOR = "track_cursor"
    SWITCH_EFFECT = "switch_effect"
    ADJUST_PARAMETER = "adjust_parameter"
    CAPTURE_SCREENSHOT = "capture_screenshot"
    TOGGLE_PAUSE = "toggle_pause"
    LAUNCH_APP = "launch_app"
    OPEN_MENU = "open_menu"
    MENU_NEXT = "menu_next"
    MENU_SELECT = "menu_select"
    CLOSE_MENU = "close_menu"
    SPEAK_HELP = "speak_help"
    SPEAK_STATUS = "speak_status"
    START_MUSIC_CHAT = "start_music_chat"
    START_LEARN_CHAT = "start_learn_chat"
    START_FREE_CHAT = "start_free_chat"
    ENTER_PAINT_MODE = "enter_paint_mode"
    EXIT_PAINT_MODE = "exit_paint_mode"


CONTINUOUS_ACTIONS = frozenset({ActionType.TRACK_CURSOR, ActionType.ADJUST_PARAMETER})


@dataclass(slots=True, frozen=True)
class ActionCommand:
    """A routed gesture action ready for execution."""

    action: ActionType
    gesture: GestureType
    hand: Handedness
    target: str | None = None
    value: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
