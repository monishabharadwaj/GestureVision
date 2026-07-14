from __future__ import annotations

"""Classifies hand poses into gesture events."""

import time
from typing import Any

from gesturevision.core.types import GestureEvent, GestureType, HandResult, Handedness
from gesturevision.gesture_recognition.debouncer import DebounceResult, GestureDebouncer
from gesturevision.gesture_recognition.finger_geometry import pinch_strength
from gesturevision.gesture_recognition.rules import get_gesture_rules
from gesturevision.input.cursor_mapper import CursorMapper


class GestureRecognizer:
    """Evaluates gesture rules on the dominant hand with debouncing."""

    def __init__(self, config: dict[str, Any]) -> None:
        gestures_cfg = config.get("gestures", config)
        self._min_confidence = float(gestures_cfg.get("min_confidence", 0.7))
        self._dominant_hand = str(gestures_cfg.get("dominant_hand", "Right"))
        self._mapper = CursorMapper(mirror=False)
        self._rules = get_gesture_rules()

        mappings = gestures_cfg.get("mappings", {})
        per_gesture: dict[GestureType, int] = {}
        for name, mapping in mappings.items():
            try:
                gesture = GestureType(name)
            except ValueError:
                continue
            per_gesture[gesture] = int(mapping.get("debounce_frames", gestures_cfg.get("debounce_frames", 8)))

        self._debouncer = GestureDebouncer(
            default_frames=int(gestures_cfg.get("debounce_frames", 8)),
            per_gesture_frames=per_gesture,
        )
        self._last_pinch_strength = 0.0

    def apply_profile_debounce(self, mappings: dict[str, Any]) -> None:
        """Override debounce timing from an accessibility profile."""
        per_gesture: dict[GestureType, int] = {}
        for name, mapping in mappings.items():
            if "debounce_frames" not in mapping:
                continue
            try:
                gesture = GestureType(name)
            except ValueError:
                continue
            per_gesture[gesture] = int(mapping["debounce_frames"])
        if per_gesture:
            self._debouncer.set_per_gesture_frames(per_gesture)

    @property
    def last_pinch_strength(self) -> float:
        return self._last_pinch_strength

    def reset(self) -> None:
        self._debouncer.reset()
        self._last_pinch_strength = 0.0

    def recognize(self, hands: list[HandResult]) -> tuple[DebounceResult, float]:
        """
        Recognize the current gesture for the dominant hand.

        Returns the debounce result and pinch strength (0 when not pinching).
        """
        hand = self._mapper.select_dominant_hand(hands, self._dominant_hand)
        if hand is None:
            self._debouncer.reset()
            return DebounceResult(GestureType.UNKNOWN, None), 0.0

        best_gesture = GestureType.UNKNOWN
        best_score = 0.0
        for rule in self._rules:
            score = rule.evaluate(hand)
            if score > best_score:
                best_score = score
                best_gesture = rule.gesture

        if best_score < self._min_confidence:
            best_gesture = GestureType.UNKNOWN
            best_score = 0.0

        pinch_strength_value = 0.0
        if best_gesture == GestureType.PINCH:
            pinch_strength_value = pinch_strength(hand.landmarks)
            self._last_pinch_strength = pinch_strength_value

        result = self._debouncer.update(
            best_gesture,
            hand=hand.handedness,
            confidence=best_score,
            timestamp=time.perf_counter(),
        )
        return result, pinch_strength_value

    def recognize_events(self, hands: list[HandResult]) -> list[GestureEvent]:
        """Protocol-compatible wrapper returning action-ready gesture events."""
        result, _ = self.recognize(hands)
        if result.action_event is not None:
            return [result.action_event]
        return []
