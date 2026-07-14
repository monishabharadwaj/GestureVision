from __future__ import annotations

"""Map normalized landmark coordinates to widget pixel space."""

from gesturevision.core.types import Handedness


class CursorMapper:
    """Converts normalized finger coordinates to pixel positions."""

    def __init__(self, mirror: bool = True) -> None:
        self._mirror = mirror

    @property
    def mirror(self) -> bool:
        return self._mirror

    def set_mirror(self, mirror: bool) -> None:
        self._mirror = mirror

    def to_pixels(
        self,
        normalized: tuple[float, float],
        width: int,
        height: int,
    ) -> tuple[int, int]:
        """Map a normalized (x, y) position to integer pixel coordinates."""
        x, y = normalized
        if self._mirror:
            x = 1.0 - x
        px = int(max(0.0, min(1.0, x)) * (width - 1))
        py = int(max(0.0, min(1.0, y)) * (height - 1))
        return px, py

    def select_dominant_hand(
        self,
        hands: list,
        dominant: str = "Right",
    ):
        """
        Pick the controlling hand based on configured dominance.

        ``dominant`` may be ``Left``, ``Right``, or ``Auto`` (highest confidence).
        """
        if not hands:
            return None
        if dominant == "Auto":
            return max(hands, key=lambda h: h.confidence)
        target: Handedness = "Right" if dominant == "Right" else "Left"
        for hand in hands:
            if hand.handedness == target:
                return hand
        return hands[0]
