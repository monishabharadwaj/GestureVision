from __future__ import annotations

"""Shared speech recognition helpers with multiple fallbacks."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

_BEAUTY_FUZZY = ("beaut", "booty", "bee you", "bee uty", "view tea", "duty")


def normalize_speech(text: str) -> str:
    return re.sub(r"[^\w\s]", "", text.lower()).strip()


def matches_beauty_trigger(text: str, triggers: list[str]) -> bool:
    """Loose matching so loud or unclear 'Beauty' still activates blind mode."""
    normalized = normalize_speech(text)
    if not normalized:
        return False

    for trigger in triggers:
        if trigger.lower() in normalized:
            return True

    for fuzzy in _BEAUTY_FUZZY:
        if fuzzy in normalized:
            return True

    if "beauty" in normalized.replace(" ", ""):
        return True

    words = normalized.split()
    return "beauty" in words


def transcribe_audio(recognizer: Any, audio: Any) -> str | None:
    """Try online then offline recognizers."""
    try:
        return recognizer.recognize_google(audio)
    except Exception:
        logger.debug("Google speech recognition failed", exc_info=True)

    if hasattr(recognizer, "recognize_sphinx"):
        try:
            return recognizer.recognize_sphinx(audio)
        except Exception:
            logger.debug("Sphinx speech recognition failed", exc_info=True)

    return None
