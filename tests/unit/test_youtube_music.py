from __future__ import annotations

"""Unit tests for direct YouTube playback URL resolution."""

from gesturevision.accessibility.youtube_music import youtube_play_url


def test_youtube_play_url_uses_watch_link_when_id_known() -> None:
    url, direct = youtube_play_url("imagine dragons", video_id="abc123xyz01")
    assert direct is True
    assert url == "https://www.youtube.com/watch?v=abc123xyz01&autoplay=1"


def test_youtube_play_url_falls_back_to_search(monkeypatch) -> None:
    monkeypatch.setattr(
        "gesturevision.accessibility.youtube_music.resolve_youtube_video_id",
        lambda _query: None,
    )
    url, direct = youtube_play_url("unknown song xyz")
    assert direct is False
    assert "results?search_query=" in url
