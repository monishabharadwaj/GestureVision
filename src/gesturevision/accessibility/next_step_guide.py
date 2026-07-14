from __future__ import annotations

"""Persistent next-step instructions for Dandelion mode."""

from dataclasses import dataclass


@dataclass(slots=True)
class GuideState:
    camera_running: bool = False
    menu_open: bool = False
    brush_mode: bool = False
    menu_highlight: str = ""
    last_voice: str = ""
    conversation_hint: str = ""


def next_step_message(state: GuideState) -> str:
    """Return a short 'what to do next' line for on-screen display."""
    if state.conversation_hint:
        return state.conversation_hint

    if state.last_voice:
        return f'YOU SAID: "{state.last_voice.upper()}"'

    if not state.camera_running:
        return "NEXT → Press START CAMERA"

    if state.menu_open:
        target = state.menu_highlight or "item"
        return f"NEXT → ✌ Peace = next  |  👍 Thumbs up = OPEN {target.upper()}  |  ✊ Fist = close"

    if state.brush_mode:
        return (
            "PAINT STUDIO → ☝ draw on your face  |  ✌ movie sketch  |  🤘 movie edge  |  "
            "👌 change 3D brush  |  👍 drop 3D object  |  🤏 brush size  |  ✊ clear"
        )

    return (
        "NEXT → POINT finger at TOUCH BAR below, hold or pinch to tap  |  "
        "SAY: play music, open youtube, open chrome, paint"
    )
