from __future__ import annotations

"""Unit tests for the ring buffer."""

from gesturevision.core.frame_buffer import RingBuffer


def test_ring_buffer_latest_overwrites() -> None:
    buf: RingBuffer[int] = RingBuffer(3)
    assert buf.latest() is None

    buf.push(1)
    buf.push(2)
    buf.push(3)
    assert buf.latest() == 3
    assert buf.count == 3

    buf.push(4)
    assert buf.latest() == 4
    assert buf.count == 3


def test_ring_buffer_clear() -> None:
    buf: RingBuffer[str] = RingBuffer(2)
    buf.push("a")
    buf.clear()
    assert buf.count == 0
    assert buf.latest() is None
