from __future__ import annotations

"""Unit tests for accessibility conversation flows."""

from gesturevision.accessibility.conversation_manager import ConversationManager, ConversationMode
from gesturevision.accessibility.learning import google_search_url


def test_music_flow_plays_direct_watch_link(monkeypatch) -> None:
    monkeypatch.setattr(
        "gesturevision.accessibility.conversation_manager.youtube_play_url",
        lambda song: (f"https://www.youtube.com/watch?v=testid12345&autoplay=1", True),
    )
    manager = ConversationManager()
    prompt = manager.start_music()
    assert "song" in prompt.lower()
    assert manager.mode == ConversationMode.MUSIC

    result = manager.handle_utterance("bohemian rhapsody")
    assert result.mode == ConversationMode.IDLE
    assert result.direct_play is True
    assert "watch?v=testid12345" in (result.open_url or "")
    assert "now playing" in result.reply.lower()


def test_learn_flow_returns_visual_detail() -> None:
    manager = ConversationManager()
    manager.start_learn()
    result = manager.handle_utterance("photosynthesis")
    assert result.mode == ConversationMode.IDLE
    assert result.reply
    assert result.visual_detail
    assert result.open_url == google_search_url("learn about photosynthesis")


def test_free_flow_routes_to_music_followup() -> None:
    manager = ConversationManager()
    manager.start_free()
    result = manager.handle_utterance("play a song on youtube")
    assert result.mode == ConversationMode.MUSIC
    assert "song" in result.reply.lower()


def test_free_flow_opens_youtube() -> None:
    manager = ConversationManager()
    manager.start_free()
    result = manager.handle_utterance("open youtube")
    assert result.mode == ConversationMode.IDLE
    assert result.open_url == "https://www.youtube.com"
