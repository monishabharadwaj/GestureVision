from __future__ import annotations

"""Application state machine for high-level operating modes."""

import logging

from gesturevision.core.events import DomainEvent, EventBus, EventType
from gesturevision.core.types import AppMode

logger = logging.getLogger(__name__)


class StateMachine:
    """Manages transitions between application modes."""

    def __init__(self, event_bus: EventBus, initial: AppMode = AppMode.LIVE) -> None:
        self._mode = initial
        self._event_bus = event_bus
        self._allowed: dict[AppMode, set[AppMode]] = {
            AppMode.LIVE: {AppMode.IMAGE_EDIT, AppMode.RECORDING, AppMode.SETTINGS, AppMode.PAUSED},
            AppMode.IMAGE_EDIT: {AppMode.LIVE, AppMode.SETTINGS, AppMode.PAUSED},
            AppMode.RECORDING: {AppMode.LIVE, AppMode.PAUSED},
            AppMode.SETTINGS: {AppMode.LIVE, AppMode.IMAGE_EDIT},
            AppMode.PAUSED: {AppMode.LIVE, AppMode.IMAGE_EDIT, AppMode.SETTINGS},
        }

    @property
    def mode(self) -> AppMode:
        return self._mode

    def can_transition(self, target: AppMode) -> bool:
        """Return whether a transition from the current mode is allowed."""
        if target == self._mode:
            return True
        return target in self._allowed.get(self._mode, set())

    def transition(self, target: AppMode) -> bool:
        """
        Transition to ``target`` if allowed.

        Returns True on success, False if the transition is rejected.
        """
        if target == self._mode:
            return True
        if not self.can_transition(target):
            logger.warning("Rejected mode transition %s → %s", self._mode.value, target.value)
            return False

        previous = self._mode
        self._mode = target
        logger.info("Mode changed: %s → %s", previous.value, target.value)
        self._event_bus.publish(
            DomainEvent(
                type=EventType.MODE_CHANGED,
                payload={"from": previous.value, "to": target.value},
            )
        )
        return True
