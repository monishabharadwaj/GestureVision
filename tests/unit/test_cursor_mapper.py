from __future__ import annotations

"""Unit tests for cursor mapping."""

from gesturevision.input.cursor_mapper import CursorMapper


def test_cursor_mapper_mirror_flips_x() -> None:
    mapper = CursorMapper(mirror=True)
    px, py = mapper.to_pixels((0.25, 0.5), width=100, height=50)
    assert px == 74
    assert py == 24


def test_cursor_mapper_without_mirror() -> None:
    mapper = CursorMapper(mirror=False)
    px, py = mapper.to_pixels((0.25, 0.5), width=100, height=50)
    assert px == 24
    assert py == 24
