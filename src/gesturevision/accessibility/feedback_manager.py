from __future__ import annotations

"""Routes accessibility feedback to TTS or on-screen captions."""

import logging
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from gesturevision.accessibility.messages import message_for_event
from gesturevision.accessibility.profile_config import ProfileSettings
from gesturevision.accessibility.tts_service import TextToSpeechService
from gesturevision.core.events import DomainEvent, EventBus, EventType
from gesturevision.core.types import AccessibilityProfile

logger = logging.getLogger(__name__)

_SUBSCRIBED_EVENTS = (
    EventType.GESTURE_DETECTED,
    EventType.ACTION_TRIGGERED,
    EventType.EFFECT_CHANGED,
    EventType.MODE_CHANGED,
    EventType.HAND_ACQUIRED,
    EventType.HAND_LOST,
    EventType.CAMERA_STATUS,
    EventType.SCREENSHOT_CAPTURED,
)


class FeedbackManager(QObject):
    """Subscribes to domain events and emits voice or visual feedback."""

    caption_requested = pyqtSignal(str, int)  # text, duration_ms

    def __init__(
        self,
        event_bus: EventBus,
        settings: ProfileSettings,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._event_bus = event_bus
        self._settings = settings
        self._tts = TextToSpeechService()
        self._last_spoken = ""

        if settings.tts_enabled:
            self._tts.start()

        for event_type in _SUBSCRIBED_EVENTS:
            event_bus.subscribe(event_type, self._on_event)

    @property
    def settings(self) -> ProfileSettings:
        return self._settings

    def apply_profile(self, settings: ProfileSettings) -> None:
        """Switch feedback behavior at runtime."""
        if self._settings.tts_enabled and not settings.tts_enabled:
            self._tts.shutdown()
        self._settings = settings
        if settings.tts_enabled and not self._tts.available:
            self._tts.start()
        self._event_bus.publish(
            DomainEvent(
                type=EventType.PROFILE_CHANGED,
                payload={"profile": settings.profile.value},
            )
        )

    def announce_welcome(self) -> None:
        """Speak or caption the profile welcome message."""
        text = self._settings.welcome.strip()
        if not text:
            return
        self._deliver(text, force=True)

    def announce(self, text: str) -> None:
        """Deliver an ad-hoc accessibility message."""
        self._deliver(text.strip(), force=True)

    def _on_event(self, event: DomainEvent) -> None:
        message = message_for_event(
            event,
            profile=self._settings.profile,
            messages_cfg=self._settings.messages,
        )
        if message:
            self._deliver(message)

    def _deliver(self, text: str, *, force: bool = False) -> None:
        if not text or self._settings.profile == AccessibilityProfile.STANDARD:
            return

        if not force and text == self._last_spoken:
            return
        self._last_spoken = text

        if self._settings.tts_enabled:
            self._tts.speak(text)
            logger.debug("TTS: %s", text)

        if self._settings.visual_captions:
            self.caption_requested.emit(text, self._settings.caption_duration_ms)
            logger.debug("Caption: %s", text)

    def shutdown(self) -> None:
        self._tts.shutdown()
        for event_type in _SUBSCRIBED_EVENTS:
            self._event_bus.unsubscribe(event_type, self._on_event)
