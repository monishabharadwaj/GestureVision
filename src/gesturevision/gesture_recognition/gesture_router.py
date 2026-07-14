from __future__ import annotations

"""Maps confirmed gesture events to executable actions via configuration."""

import logging
from typing import Any

from gesturevision.core.types import GestureEvent, GestureType, Handedness
from gesturevision.gesture_recognition.actions import ActionCommand, ActionType

logger = logging.getLogger(__name__)


class GestureRouter:
    """Translate gesture events into action commands using ``gestures.yaml`` mappings."""

    def __init__(self, config: dict[str, Any]) -> None:
        gestures_cfg = config.get("gestures", config)
        self._mappings: dict[GestureType, dict[str, Any]] = {}
        for name, mapping in gestures_cfg.get("mappings", {}).items():
            try:
                gesture = GestureType(name)
            except ValueError:
                logger.warning("Unknown gesture in config: %s", name)
                continue
            self._mappings[gesture] = mapping

    def route(
        self,
        event: GestureEvent,
        *,
        pinch_strength: float = 0.0,
    ) -> ActionCommand | None:
        mapping = self._mappings.get(event.gesture)
        if mapping is None:
            return None

        action_name = str(mapping.get("action", ""))
        try:
            action = ActionType(action_name)
        except ValueError:
            logger.warning("Unknown action '%s' for gesture %s", action_name, event.gesture.value)
            return None

        value = None
        if action == ActionType.ADJUST_PARAMETER:
            value = pinch_strength

        return ActionCommand(
            action=action,
            gesture=event.gesture,
            hand=event.hand,
            target=mapping.get("target"),
            value=value,
            metadata={"confidence": event.confidence},
        )

    def apply_profile_mappings(self, mappings: dict[str, Any]) -> None:
        """Replace gesture mappings for an accessibility profile."""
        self._mappings.clear()
        for name, mapping in mappings.items():
            try:
                gesture = GestureType(name)
            except ValueError:
                logger.warning("Unknown profile gesture: %s", name)
                continue
            self._mappings[gesture] = mapping
        logger.info("Applied %d profile gesture mappings", len(self._mappings))

    def route_continuous(
        self,
        gesture: GestureType,
        hand: Handedness,
        *,
        pinch_strength: float = 0.0,
    ) -> ActionCommand | None:
        """Build continuous action commands for per-frame gestures."""
        mapping = self._mappings.get(gesture)
        if mapping is None:
            return None

        action_name = str(mapping.get("action", ""))
        try:
            action = ActionType(action_name)
        except ValueError:
            return None

        if action not in {ActionType.TRACK_CURSOR, ActionType.ADJUST_PARAMETER}:
            return None

        value = pinch_strength if action == ActionType.ADJUST_PARAMETER else None
        return ActionCommand(
            action=action,
            gesture=gesture,
            hand=hand,
            target=mapping.get("target"),
            value=value,
        )
