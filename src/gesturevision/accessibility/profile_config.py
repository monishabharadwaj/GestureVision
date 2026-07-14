from __future__ import annotations

"""Accessibility profile configuration."""

from dataclasses import dataclass, field
from typing import Any

from gesturevision.core.types import AccessibilityProfile


@dataclass(slots=True)
class ProfileSettings:
    """Runtime settings for an accessibility profile."""

    profile: AccessibilityProfile
    display_name: str = ""
    subtitle: str = ""
    tts_enabled: bool = False
    visual_captions: bool = False
    caption_duration_ms: int = 4000
    simplified_ui: bool = False
    audio_only: bool = False
    hide_video: bool = False
    theme: str = "dark"
    welcome: str = ""
    reduced_effects: list[str] = field(default_factory=list)
    gesture_mappings: dict[str, Any] = field(default_factory=dict)
    gesture_menu: list[str] = field(default_factory=list)
    touch_bar: list[str] = field(default_factory=list)
    apps: dict[str, Any] = field(default_factory=dict)
    auto_start_camera: bool = False
    messages: dict[str, Any] = field(default_factory=dict)

    @property
    def is_accessibility_mode(self) -> bool:
        return self.profile != AccessibilityProfile.STANDARD


def load_profile_settings(
    config: dict[str, Any],
    profile: AccessibilityProfile,
) -> ProfileSettings:
    """Build profile settings from ``accessibility.yaml``."""
    root = config.get("accessibility", config)
    profiles = root.get("profiles", {})
    messages = root.get("messages", {})
    apps = root.get("apps", {})

    if profile == AccessibilityProfile.STANDARD:
        return ProfileSettings(profile=profile, messages=messages, apps=apps)

    key = profile.value
    entry = profiles.get(key, {})
    return ProfileSettings(
        profile=profile,
        display_name=str(entry.get("display_name", key.title())),
        subtitle=str(entry.get("subtitle", "")),
        tts_enabled=bool(entry.get("tts_enabled", False)),
        visual_captions=bool(entry.get("visual_captions", False)),
        caption_duration_ms=int(entry.get("caption_duration_ms", 4000)),
        simplified_ui=bool(entry.get("simplified_ui", True)),
        audio_only=bool(entry.get("audio_only", False)),
        hide_video=bool(entry.get("hide_video", False)),
        theme=str(entry.get("theme", "accessibility_high_contrast")),
        welcome=str(entry.get("welcome", "")),
        reduced_effects=[str(name) for name in entry.get("reduced_effects", [])],
        gesture_mappings=dict(entry.get("gestures", {})),
        gesture_menu=[str(item) for item in entry.get("gesture_menu", [])],
        touch_bar=[str(item) for item in entry.get("touch_bar", entry.get("gesture_menu", []))],
        apps=apps,
        auto_start_camera=bool(entry.get("auto_start_camera", False)),
        messages=messages,
    )
