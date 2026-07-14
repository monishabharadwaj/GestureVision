from __future__ import annotations

"""Simple topic explanations for the learn conversation flow."""

import json
import logging
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)


def explain_topic(topic: str, *, max_chars: int = 420) -> str:
    """Return a short spoken/visual explanation for a topic."""
    cleaned = topic.strip()
    if not cleaned:
        return "I did not catch the topic. Please say what you want to learn."

    wiki = _fetch_wikipedia_summary(cleaned, max_chars=max_chars)
    if wiki:
        return wiki

    return (
        f"You asked about {cleaned}. "
        f"{cleaned.title()} is something you can explore online. "
        f"I opened a search to help you learn more."
    )


def _fetch_wikipedia_summary(topic: str, *, max_chars: int = 420) -> str | None:
    slug = urllib.parse.quote(topic.replace(" ", "_"))
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{slug}"
    try:
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "GestureVision-AI/1.0"},
        )
        with urllib.request.urlopen(request, timeout=4) as response:
            data = json.loads(response.read().decode("utf-8"))
        extract = str(data.get("extract", "")).strip()
        if extract:
            limit = max(120, max_chars)
            if len(extract) > limit:
                extract = extract[:limit].rsplit(" ", 1)[0] + "..."
            return extract
    except Exception:
        logger.debug("Wikipedia lookup failed for %s", topic, exc_info=True)
    return None


def youtube_search_url(query: str) -> str:
    encoded = urllib.parse.quote_plus(query.strip())
    return f"https://www.youtube.com/results?search_query={encoded}"


def google_search_url(query: str) -> str:
    encoded = urllib.parse.quote_plus(query.strip())
    return f"https://www.google.com/search?q={encoded}"
