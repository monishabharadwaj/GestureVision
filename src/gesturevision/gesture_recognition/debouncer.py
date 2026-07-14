from __future__ import annotations

"""Temporal debouncing for stable gesture detection and one-shot actions."""

from dataclasses import dataclass

from gesturevision.core.types import GestureEvent, GestureType, Handedness


@dataclass(slots=True)
class DebounceResult:
    """Output of one debouncer update."""

    display_gesture: GestureType
    action_event: GestureEvent | None


class GestureDebouncer:
    """
    Stabilize gesture detection and gate one-shot action triggers.

    Continuous gestures (index finger, pinch) display immediately.
    One-shot actions fire once per gesture hold after the debounce threshold.
    """

    def __init__(
        self,
        default_frames: int = 8,
        per_gesture_frames: dict[GestureType, int] | None = None,
    ) -> None:
        self._default_frames = max(1, default_frames)
        self._per_gesture_frames = per_gesture_frames or {}
        self._tracking = GestureType.UNKNOWN
        self._streak = 0
        self._action_fired = False

    def reset(self) -> None:
        self._tracking = GestureType.UNKNOWN
        self._streak = 0
        self._action_fired = False

    def set_per_gesture_frames(self, frames: dict[GestureType, int]) -> None:
        """Replace per-gesture debounce thresholds (e.g. accessibility profile)."""
        self._per_gesture_frames = dict(frames)
        self.reset()

    def _threshold(self, gesture: GestureType) -> int:
        frames = self._per_gesture_frames.get(gesture, self._default_frames)
        return 1 if frames <= 0 else frames

    def _is_continuous_only(self, gesture: GestureType) -> bool:
        """Gestures that should never emit one-shot action events."""
        if gesture == GestureType.INDEX_FINGER:
            return True
        if gesture == GestureType.PINCH:
            return self._per_gesture_frames.get(GestureType.PINCH, self._default_frames) <= 0
        return False

    def update(
        self,
        gesture: GestureType,
        *,
        hand: Handedness,
        confidence: float,
        timestamp: float,
    ) -> DebounceResult:
        if gesture == GestureType.UNKNOWN:
            self.reset()
            return DebounceResult(display_gesture=GestureType.UNKNOWN, action_event=None)

        if gesture == self._tracking:
            self._streak += 1
        else:
            self._tracking = gesture
            self._streak = 1
            self._action_fired = False

        threshold = self._threshold(gesture)
        display = gesture if self._streak >= min(threshold, 2) else gesture

        action_event = None
        if self._streak >= threshold and not self._action_fired:
            if not self._is_continuous_only(gesture):
                action_event = GestureEvent(
                    gesture=gesture,
                    hand=hand,
                    confidence=confidence,
                    timestamp=timestamp,
                )
                self._action_fired = True

        return DebounceResult(display_gesture=display, action_event=action_event)
