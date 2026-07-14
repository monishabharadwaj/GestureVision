from __future__ import annotations

"""Unit tests for picture/ASL pictograph cards."""

from gesturevision.accessibility.picture_cards import (
    card_for_action,
    card_for_gesture,
    card_for_text,
    card_by_id,
)


def test_card_for_rock_gesture() -> None:
    card = card_for_gesture("rock_sign")
    assert card is not None
    assert card.emoji == "🎵"
    assert card.pose == "🤘"


def test_card_for_music_action() -> None:
    card = card_for_action("start_music_chat")
    assert card is not None
    assert card.card_id == "music"


def test_card_for_launch_chrome() -> None:
    card = card_for_action("launch_app", "chrome")
    assert card is not None
    assert card.card_id == "chrome"


def test_card_for_text_keyword() -> None:
    card = card_for_text("YouTube music — what song would you like?")
    assert card is not None
    assert card.card_id in {"music", "youtube"}


def test_card_by_id_mesh() -> None:
    card = card_by_id("mesh")
    assert card is not None
    assert card.pose == "🙌"


def test_peace_vs_x_sign_cards_differ() -> None:
    peace = card_for_gesture("peace")
    x_sign = card_for_gesture("x_sign")
    assert peace is not None and x_sign is not None
    assert peace.card_id == "learn"
    assert x_sign.card_id == "done"
