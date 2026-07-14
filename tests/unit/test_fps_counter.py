from __future__ import annotations

"""Unit tests for FPS counter."""

from gesturevision.performance.fps_counter import FpsCounter


def test_fps_counter_returns_zero_until_two_ticks() -> None:
    counter = FpsCounter()
    assert counter.tick(0.0) == 0.0
    assert counter.tick(0.1) > 0.0


def test_fps_counter_reset() -> None:
    counter = FpsCounter()
    counter.tick(0.0)
    counter.tick(0.5)
    counter.reset()
    assert counter.tick(1.0) == 0.0
