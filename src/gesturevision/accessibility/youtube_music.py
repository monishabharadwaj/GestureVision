from __future__ import annotations

"""Resolve a song query to a direct YouTube watch URL."""

import logging
import re
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

_VIDEO_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{11}$")
_SEARCH_PATTERNS = (
    re.compile(r'"videoId":"([a-zA-Z0-9_-]{11})"'),
    re.compile(r'"url":"/watch\?v=([a-zA-Z0-9_-]{11})"'),
    re.compile(r"watch\?v=([a-zA-Z0-9_-]{11})"),
)


def resolve_youtube_video_id(query: str) -> str | None:
    """Return the first matching YouTube video id for a song query."""
    cleaned = query.strip()
    if not cleaned:
        return None

    encoded = urllib.parse.quote_plus(cleaned)
    url = f"https://www.youtube.com/results?search_query={encoded}&sp=EgIQAQ%253D%253D"
    try:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        with urllib.request.urlopen(request, timeout=8) as response:
            html = response.read().decode("utf-8", errors="ignore")
    except Exception:
        logger.debug("YouTube search lookup failed for %s", cleaned, exc_info=True)
        return None

    seen: set[str] = set()
    for pattern in _SEARCH_PATTERNS:
        for match in pattern.finditer(html):
            video_id = match.group(1)
            if video_id in seen or not _VIDEO_ID_RE.match(video_id):
                continue
            seen.add(video_id)
            return video_id
    return None


def youtube_play_url(query: str, *, video_id: str | None = None) -> tuple[str, bool]:
    """
    Build a URL that opens the top song match and tries to autoplay.

    Returns ``(url, direct_play)`` where ``direct_play`` is True when a watch
    link was resolved instead of a search-results page.
    """
    cleaned = query.strip()
    resolved = video_id or resolve_youtube_video_id(cleaned)
    if resolved:
        return f"https://www.youtube.com/watch?v={resolved}&autoplay=1", True
    encoded = urllib.parse.quote_plus(cleaned)
    return f"https://www.youtube.com/results?search_query={encoded}", False
