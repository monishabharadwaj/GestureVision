from __future__ import annotations

"""Lightweight in-process pub/sub for cross-module communication."""

import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)

EventHandler = Callable[["DomainEvent"], None]


class EventType(str, Enum):
    """Well-known domain event types."""

    APP_STARTED = "app.started"
    APP_STOPPING = "app.stopping"
    MODE_CHANGED = "mode.changed"
    GESTURE_DETECTED = "gesture.detected"
    EFFECT_CHANGED = "effect.changed"
    METRICS_UPDATED = "metrics.updated"
    CAMERA_STATUS = "camera.status"
    HAND_LOST = "hand.lost"
    HAND_ACQUIRED = "hand.acquired"
    ACTION_TRIGGERED = "action.triggered"
    SCREENSHOT_CAPTURED = "screenshot.captured"
    ERROR = "error"
    PROFILE_CHANGED = "profile.changed"
    FEEDBACK_MESSAGE = "feedback.message"


@dataclass(slots=True, frozen=True)
class DomainEvent:
    """Immutable domain event payload."""

    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)


class EventBus:
    """Simple synchronous event bus for in-process publishers and subscribers."""

    def __init__(self) -> None:
        self._subscribers: dict[EventType, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Register a handler for an event type."""
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
            logger.debug("Subscribed %s to %s", handler, event_type.value)

    def unsubscribe(self, event_type: EventType, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def publish(self, event: DomainEvent) -> None:
        """Dispatch an event to all matching subscribers."""
        handlers = list(self._subscribers.get(event.type, []))
        for handler in handlers:
            try:
                handler(event)
            except Exception:
                logger.exception(
                    "Event handler failed for %s: %s",
                    event.type.value,
                    handler,
                )

    def clear(self) -> None:
        """Remove all subscribers (useful for tests and shutdown)."""
        self._subscribers.clear()
