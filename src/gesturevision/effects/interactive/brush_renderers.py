from __future__ import annotations

"""Brush stroke rendering styles."""

import cv2
import numpy as np

from gesturevision.core.types import BGRImage


def render_neon_stroke(
    layer: np.ndarray,
    position: tuple[int, int],
    radius: int,
    color: tuple[int, int, int],
    core: tuple[int, int, int],
    last_pixel: tuple[int, int] | None,
    depth_offset: int = 4,
) -> None:
    height, width = layer.shape[:2]
    px, py = position
    shadow = (min(width - 1, px + depth_offset), min(height - 1, py + depth_offset))
    _stroke(layer, shadow, radius, (20, 10, 40), last_pixel)
    _stroke(layer, position, radius, color, last_pixel)
    cv2.circle(layer, position, max(2, radius // 3), core, -1, lineType=cv2.LINE_AA)


def render_soft_stroke(
    layer: np.ndarray,
    position: tuple[int, int],
    radius: int,
    color: tuple[int, int, int],
    core: tuple[int, int, int],
    last_pixel: tuple[int, int] | None,
    **_kwargs: object,
) -> None:
    soft_color = tuple(int(c * 0.65) for c in color)
    _stroke(layer, position, int(radius * 1.4), soft_color, last_pixel)
    _stroke(layer, position, radius, color, last_pixel)


def render_tube3d_stroke(
    layer: np.ndarray,
    position: tuple[int, int],
    radius: int,
    color: tuple[int, int, int],
    core: tuple[int, int, int],
    last_pixel: tuple[int, int] | None,
    **_kwargs: object,
) -> None:
    """Thick tube with highlight and shadow for a 3D extruded look."""
    px, py = position
    shadow = (px + 5, py + 6)
    highlight = (px - 3, py - 4)
    dark = tuple(max(0, int(c * 0.25)) for c in color)
    bright = tuple(min(255, int(c * 1.2)) for c in core)

    if last_pixel is not None:
        cv2.line(layer, last_pixel, shadow, dark, thickness=max(4, radius + 4), lineType=cv2.LINE_AA)
        cv2.line(layer, last_pixel, position, color, thickness=max(3, radius + 2), lineType=cv2.LINE_AA)
        cv2.line(layer, last_pixel, highlight, bright, thickness=max(2, radius // 2), lineType=cv2.LINE_AA)
    cv2.circle(layer, shadow, radius, dark, -1, lineType=cv2.LINE_AA)
    cv2.circle(layer, position, radius, color, -1, lineType=cv2.LINE_AA)
    cv2.circle(layer, highlight, max(2, radius // 3), bright, -1, lineType=cv2.LINE_AA)


def render_sparkle_stroke(
    layer: np.ndarray,
    position: tuple[int, int],
    radius: int,
    color: tuple[int, int, int],
    core: tuple[int, int, int],
    last_pixel: tuple[int, int] | None,
    **_kwargs: object,
) -> None:
    _stroke(layer, position, radius, color, last_pixel)
    for dx, dy in ((-radius, 0), (radius, 0), (0, -radius), (0, radius)):
        spark_pos = (position[0] + dx, position[1] + dy)
        cv2.circle(layer, spark_pos, max(2, radius // 4), core, -1, lineType=cv2.LINE_AA)


def _stroke(
    layer: np.ndarray,
    position: tuple[int, int],
    radius: int,
    color: tuple[int, int, int],
    last_pixel: tuple[int, int] | None,
) -> None:
    cv2.circle(layer, position, max(2, radius // 2), color, -1, lineType=cv2.LINE_AA)
    if last_pixel is not None:
        cv2.line(
            layer,
            last_pixel,
            position,
            color,
            thickness=max(3, radius),
            lineType=cv2.LINE_AA,
        )


def finalize_glow(layer: np.ndarray, blur_k: int, intensity: float) -> BGRImage:
    if blur_k % 2 == 0:
        blur_k += 1
    glow = cv2.GaussianBlur(layer, (blur_k, blur_k), 0)
    return glow * intensity


BRUSH_TYPES: dict[str, object] = {
    "neon": render_neon_stroke,
    "soft": render_soft_stroke,
    "tube3d": render_tube3d_stroke,
    "sparkle": render_sparkle_stroke,
}

BRUSH_COLOR_PRESETS: dict[str, tuple[int, int, int]] = {
    "neon_pink": (255, 80, 255),
    "cyan": (255, 220, 80),
    "gold": (0, 200, 255),
    "lime": (80, 255, 120),
    "white": (255, 255, 255),
    "red": (80, 80, 255),
}
