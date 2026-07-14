from __future__ import annotations

"""Pre-allocated ring buffer for frames — avoids per-frame allocations."""

import threading
from typing import Generic, TypeVar

T = TypeVar("T")


class RingBuffer(Generic[T]):
    """
    Thread-safe fixed-size ring buffer.

    Writers overwrite the oldest slot when full.
    Readers can fetch the newest item without draining history.
    """

    def __init__(self, capacity: int) -> None:
        if capacity < 1:
            raise ValueError("RingBuffer capacity must be >= 1")
        self._capacity = capacity
        self._slots: list[T | None] = [None] * capacity
        self._write_index = 0
        self._count = 0
        self._lock = threading.Lock()

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def count(self) -> int:
        with self._lock:
            return self._count

    def push(self, item: T) -> None:
        """Store an item, overwriting the oldest when full."""
        with self._lock:
            self._slots[self._write_index] = item
            self._write_index = (self._write_index + 1) % self._capacity
            self._count = min(self._count + 1, self._capacity)

    def latest(self) -> T | None:
        """Return the most recently pushed item, or None if empty."""
        with self._lock:
            if self._count == 0:
                return None
            index = (self._write_index - 1) % self._capacity
            return self._slots[index]

    def clear(self) -> None:
        """Remove all buffered items."""
        with self._lock:
            self._slots = [None] * self._capacity
            self._write_index = 0
            self._count = 0
