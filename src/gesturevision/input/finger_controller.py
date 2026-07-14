from __future__ import annotations

"""Index finger tracking for cursor control."""

from gesturevision.hand_tracking import landmarks as lm
from gesturevision.input.cursor_mapper import CursorMapper


class FingerController:
    """Tracks the index fingertip of the dominant hand."""

    def __init__(self, dominant_hand: str = "Right", mirror: bool = True) -> None:
        self._mapper = CursorMapper(mirror=mirror)
        self._dominant_hand = dominant_hand
        self._last_position: tuple[float, float] | None = None

    @property
    def dominant_hand(self) -> str:
        return self._dominant_hand

    def set_dominant_hand(self, hand: str) -> None:
        self._dominant_hand = hand

    def set_mirror(self, mirror: bool) -> None:
        self._mapper.set_mirror(mirror)

    @property
    def last_position(self) -> tuple[float, float] | None:
        return self._last_position

    def update(self, hands) -> tuple[float, float] | None:
        """Return the normalized index fingertip of the dominant hand."""
        hand = self._mapper.select_dominant_hand(hands, self._dominant_hand)
        if hand is None:
            self._last_position = None
            return None

        tip = hand.landmarks[lm.INDEX_TIP]
        self._last_position = (float(tip[0]), float(tip[1]))
        return self._last_position

    def pixel_position(self, width: int, height: int) -> tuple[int, int] | None:
        """Return the last fingertip position in pixel coordinates."""
        if self._last_position is None:
            return None
        return self._mapper.to_pixels(self._last_position, width, height)
