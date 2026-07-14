from __future__ import annotations

"""Natural-language voice command matching for Dandelion (and Beauty)."""

import re
from typing import Any

_OPEN_VERBS = ("open", "launch", "start", "go", "play", "run", "show")


def build_phrase_map(
    voice_commands: dict[str, list[str]],
    apps: dict[str, Any],
) -> dict[str, list[str]]:
    """Merge config phrases with app labels for flexible speech."""
    merged: dict[str, list[str]] = {key: list(values) for key, values in voice_commands.items()}

    for app_id, entry in apps.items():
        label = str(entry.get("label", app_id)).lower()
        phrases = merged.setdefault(app_id, [])
        for candidate in (
            app_id,
            label,
            f"open {label}",
            f"open {app_id}",
            f"play {label}",
            f"launch {label}",
            f"go to {label}",
        ):
            if candidate not in phrases:
                phrases.append(candidate)

    music = merged.setdefault("music", [])
    for phrase in ("music", "play music", "song", "songs", "spotify", "play song"):
        if phrase not in music:
            music.append(phrase)

    return merged


def match_spoken_command(text: str, phrase_map: dict[str, list[str]]) -> str | None:
    """Pick the best command from free-form speech."""
    normalized = re.sub(r"[^\w\s]", "", text.lower()).strip()
    if not normalized:
        return None

    ranked: list[tuple[int, str]] = []
    for command_id, variants in phrase_map.items():
        for phrase in sorted(variants, key=len, reverse=True):
            if phrase in normalized:
                ranked.append((len(phrase), command_id))
                break

    if ranked:
        ranked.sort(reverse=True)
        return ranked[0][1]

    # Fallback keyword hits
    tokens = set(normalized.split())
    if tokens & {"youtube", "tube"}:
        return "youtube"
    if tokens & {"chrome", "google", "browser"}:
        return "chrome"
    if tokens & {"edge", "microsoft"}:
        return "edge"
    if tokens & {"firefox", "mozilla"}:
        return "firefox"
    if tokens & {"paint", "brush", "draw", "drawing"}:
        return "paint"
    if tokens & {"music", "song", "spotify"}:
        return "music"
    if tokens & {"help", "instructions"}:
        return "help"
    if tokens & {"menu", "navigation"}:
        return "menu"
    if tokens & {"camera", "original", "live"}:
        return "original"
    return None
