from __future__ import annotations

"""Pictograph cards for users who cannot read — emoji + hand-pose symbols."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PictureCard:
    """A single picture-based UI token — no reading required."""

    card_id: str
    emoji: str
    pose: str
    color: str
    label: str = ""


# Gesture → pictograph (pose = how to hold your hand)
GESTURE_CARDS: dict[str, PictureCard] = {
    "rock_sign": PictureCard("music", "🎵", "🤘", "#0044cc", "music"),
    "peace": PictureCard("learn", "📚", "✌", "#006600", "learn"),
    "ok_sign": PictureCard("ask", "💬", "👌", "#6600aa", "ask"),
    "thumbs_up": PictureCard("paint", "🎨", "👍", "#cc6600", "paint"),
    "index_finger": PictureCard("touch", "👆", "☝", "#0066cc", "touch"),
    "closed_fist": PictureCard("exit", "🔙", "👊", "#333333", "back"),
    "pinch": PictureCard("size", "🤏", "🤏", "#444444", "size"),
    "x_sign": PictureCard("done", "✅", "❌", "#990000", "done"),
}

# Apps / launch targets
APP_CARDS: dict[str, PictureCard] = {
    "chrome": PictureCard("chrome", "🌐", "☝", "#2266dd", "web"),
    "youtube": PictureCard("youtube", "▶️", "☝", "#cc0000", "video"),
    "music": PictureCard("music", "🎵", "🤘", "#0044cc", "music"),
    "paint": PictureCard("paint", "🎨", "👍", "#cc6600", "paint"),
    "edge": PictureCard("edge", "🌐", "☝", "#0078d4", "web"),
    "firefox": PictureCard("firefox", "🦊", "☝", "#e66000", "web"),
}

# Action names from ActionType
ACTION_CARDS: dict[str, PictureCard] = {
    "start_music_chat": GESTURE_CARDS["rock_sign"],
    "start_learn_chat": GESTURE_CARDS["peace"],
    "start_free_chat": GESTURE_CARDS["ok_sign"],
    "enter_paint_mode": GESTURE_CARDS["thumbs_up"],
    "exit_paint_mode": GESTURE_CARDS["closed_fist"],
    "launch_app": PictureCard("open", "🚀", "☝", "#228822", "open"),
    "capture_screenshot": PictureCard("photo", "📷", "👍", "#555555", "photo"),
    "toggle_pause": PictureCard("pause", "⏸", "✊", "#555555", "pause"),
}

LIVE_POSE_STRIP: tuple[PictureCard, ...] = (
    GESTURE_CARDS["rock_sign"],
    GESTURE_CARDS["peace"],
    GESTURE_CARDS["ok_sign"],
    GESTURE_CARDS["thumbs_up"],
    GESTURE_CARDS["index_finger"],
    PictureCard("mesh", "🙌", "🙌", "#00aacc", "2 hands"),
)

PAINT_POSE_STRIP: tuple[PictureCard, ...] = (
    PictureCard("draw", "✏️", "☝", "#ff66cc", "draw"),
    PictureCard("brush", "🖌", "👌", "#66ccff", "brush"),
    PictureCard("ink", "🎨", "🤘", "#ffcc00", "ink"),
    PictureCard("bg", "🎬", "✌", "#99ff99", "look"),
    PictureCard("sticker", "⭐", "👍", "#ff9900", "3d"),
    GESTURE_CARDS["x_sign"],
)

LIVE_ACTION_BOARD: tuple[str, ...] = ("music", "learn", "ask", "paint", "chrome", "mesh")


def card_by_id(card_id: str) -> PictureCard | None:
    for pool in (GESTURE_CARDS, APP_CARDS, ACTION_CARDS):
        for card in pool.values():
            if card.card_id == card_id:
                return card
    extras = {
        "mesh": PictureCard("mesh", "🙌", "🙌", "#00aacc", "mesh"),
        "learn": GESTURE_CARDS["peace"],
        "ask": GESTURE_CARDS["ok_sign"],
        "draw": PAINT_POSE_STRIP[0],
        "brush": PAINT_POSE_STRIP[1],
        "ink": PAINT_POSE_STRIP[2],
        "background": PAINT_POSE_STRIP[3],
        "sticker": PAINT_POSE_STRIP[4],
        "done": GESTURE_CARDS["x_sign"],
    }
    return extras.get(card_id)


def card_for_gesture(gesture: str) -> PictureCard | None:
    return GESTURE_CARDS.get(gesture.strip().lower())


def card_for_action(action: str, target: str | None = None) -> PictureCard | None:
    normalized = action.strip().lower()
    if normalized == "launch_app" and target:
        return APP_CARDS.get(str(target).strip().lower()) or ACTION_CARDS.get("launch_app")
    return ACTION_CARDS.get(normalized)


def card_for_text(text: str) -> PictureCard | None:
    """Best-effort pictograph from a caption string."""
    lowered = text.lower()
    keyword_map: list[tuple[str, str]] = [
        ("music", "music"),
        ("youtube", "youtube"),
        ("learn", "learn"),
        ("paint", "paint"),
        ("chrome", "chrome"),
        ("mesh", "mesh"),
        ("3d", "mesh"),
        ("touch", "touch"),
        ("screenshot", "photo"),
        ("paused", "pause"),
        ("opening", "open"),
        ("song", "music"),
        ("brush", "brush"),
        ("done", "done"),
        ("live mode", "exit"),
    ]
    for keyword, card_id in keyword_map:
        if keyword in lowered:
            return card_by_id(card_id)
    for gesture, card in GESTURE_CARDS.items():
        if gesture.replace("_", " ") in lowered:
            return card
    return None
