from __future__ import annotations

"""Rolling FPS measurement for the processing loop."""

from collections import deque


class FpsCounter:
    """Compute frames-per-second from recent frame timestamps."""

    def __init__(self, window_size: int = 30) -> None:
        self._timestamps: deque[float] = deque(maxlen=window_size)

    def reset(self) -> None:
        self._timestamps.clear()

    def tick(self, timestamp: float) -> float:
        """Record a frame timestamp and return the current FPS estimate."""
        self._timestamps.append(timestamp)
        if len(self._timestamps) < 2:
            return 0.0

        elapsed = self._timestamps[-1] - self._timestamps[0]
        if elapsed <= 0.0:
            return 0.0
        return (len(self._timestamps) - 1) / elapsed
