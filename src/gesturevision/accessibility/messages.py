from __future__ import annotations

"""Map domain events to human-friendly accessibility messages."""

from typing import Any

from gesturevision.core.events import DomainEvent, EventType
from gesturevision.core.types import AccessibilityProfile
from gesturevision.gesture_recognition.actions import ActionType


def message_for_event(
    event: DomainEvent,
    *,
    profile: AccessibilityProfile,
    messages_cfg: dict[str, Any],
) -> str | None:
    """Return a speakable or captioned message for an event, if any."""
    if profile == AccessibilityProfile.STANDARD:
        return None

    gestures = messages_cfg.get("gestures", {})
    actions = messages_cfg.get("actions", {})
    events = messages_cfg.get("events", {})

    if event.type == EventType.GESTURE_DETECTED:
        gesture = str(event.payload.get("gesture", ""))
        return str(gestures.get(gesture, gesture.replace("_", " ").title()))

    if event.type == EventType.ACTION_TRIGGERED:
        action = str(event.payload.get("action", ""))
        target = event.payload.get("target")
        label = event.payload.get("label")
        if action == ActionType.SWITCH_EFFECT.value and target:
            template = actions.get("switch_effect", "Switched to {target}")
            return template.format(target=str(target).replace("_", " "))
        if action == ActionType.CAPTURE_SCREENSHOT.value:
            return str(actions.get("capture_screenshot", "Screenshot saved"))
        if action == ActionType.TOGGLE_PAUSE.value:
            return str(actions.get("toggle_pause", "Paused"))
        if action == ActionType.ADJUST_PARAMETER.value:
            return str(actions.get("adjust_parameter", "Size adjusted"))
        if action == ActionType.LAUNCH_APP.value:
            template = actions.get("launch_app", "Opening {target}")
            return template.format(target=str(label or target or "app"))
        if action == ActionType.OPEN_MENU.value:
            return str(actions.get("open_menu", "Menu opened"))
        if action == ActionType.MENU_NEXT.value:
            template = actions.get("menu_next", "Next: {target}")
            return template.format(target=str(label or target or "item"))
        if action == ActionType.MENU_SELECT.value:
            template = actions.get("menu_select", "Opening {target}")
            return template.format(target=str(label or target or "item"))
        if action == ActionType.CLOSE_MENU.value:
            return str(actions.get("close_menu", "Menu closed"))
        if action == ActionType.SPEAK_HELP.value:
            return str(actions.get("speak_help", "Help"))
        if action == ActionType.SPEAK_STATUS.value:
            return str(actions.get("speak_status", "Status"))
        if action == ActionType.START_MUSIC_CHAT.value:
            return str(actions.get("start_music_chat", "Music mode. What song?"))
        if action == ActionType.START_LEARN_CHAT.value:
            return str(actions.get("start_learn_chat", "What do you want to learn?"))
        if action == ActionType.START_FREE_CHAT.value:
            return str(actions.get("start_free_chat", "Tell me what you want"))
        if action == "conversation":
            return str(event.payload.get("label", ""))
        return None

    if event.type == EventType.EFFECT_CHANGED:
        effect = str(event.payload.get("effect", ""))
        template = events.get("effect_changed", "Now using {effect}")
        return template.format(effect=effect.replace("_", " "))

    if event.type == EventType.HAND_ACQUIRED:
        return str(events.get("hand_acquired", "Hand detected"))

    if event.type == EventType.HAND_LOST:
        return str(events.get("hand_lost", "Hand lost"))

    if event.type == EventType.CAMERA_STATUS:
        status = str(event.payload.get("status", ""))
        if status == "running":
            return str(events.get("camera_started", "Camera started"))
        if status == "stopped":
            return str(events.get("camera_stopped", "Camera stopped"))
        return None

    if event.type == EventType.MODE_CHANGED:
        mode = str(event.payload.get("to", ""))
        if mode == "live":
            return str(events.get("resumed", "Resumed"))
        if mode == "paused":
            return str(actions.get("toggle_pause", "Paused"))
        return None

    if event.type == EventType.SCREENSHOT_CAPTURED:
        return str(actions.get("capture_screenshot", "Screenshot saved"))

    return None
