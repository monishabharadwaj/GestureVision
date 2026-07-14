from __future__ import annotations

"""3D-style stickers placed on the paint canvas with gestures."""

import cv2
import numpy as np

from gesturevision.core.types import BGRImage


def draw_sphere(image: BGRImage, center: tuple[int, int], radius: int, color: tuple[int, int, int]) -> None:
    """Draw a shaded sphere for a simple 3D object."""
    x, y = center
    cv2.circle(image, center, radius, color, -1, lineType=cv2.LINE_AA)
    highlight = tuple(min(255, int(c * 1.35)) for c in color)
    cv2.circle(image, (x - radius // 3, y - radius // 3), max(3, radius // 3), highlight, -1, lineType=cv2.LINE_AA)
    shadow = tuple(max(0, int(c * 0.45)) for c in color)
    cv2.ellipse(
        image,
        (x + radius // 4, y + radius // 3),
        (max(3, radius // 2), max(2, radius // 4)),
        0,
        0,
        360,
        shadow,
        -1,
        lineType=cv2.LINE_AA,
    )


def draw_cube(image: BGRImage, center: tuple[int, int], size: int, color: tuple[int, int, int]) -> None:
    """Draw an isometric cube."""
    x, y = center
    half = size // 2
    front = np.array(
        [
            [x - half, y - half],
            [x + half, y - half],
            [x + half, y + half],
            [x - half, y + half],
        ],
        dtype=np.int32,
    )
    top = front + np.array([[0, -half // 2], [half // 2, -half], [half // 2, -half // 2], [0, -half // 2]])
    side = front + np.array([[half // 2, -half // 2], [half, 0], [half, half // 2], [half // 2, half // 2]])

    dark = tuple(max(0, int(c * 0.55)) for c in color)
    bright = tuple(min(255, int(c * 1.15)) for c in color)
    cv2.fillPoly(image, [side], dark, lineType=cv2.LINE_AA)
    cv2.fillPoly(image, [top], bright, lineType=cv2.LINE_AA)
    cv2.fillPoly(image, [front], color, lineType=cv2.LINE_AA)


def draw_star(image: BGRImage, center: tuple[int, int], radius: int, color: tuple[int, int, int]) -> None:
    """Draw a sparkle star sticker."""
    x, y = center
    points = []
    for i in range(10):
        angle = np.pi / 2 + i * np.pi / 5
        dist = radius if i % 2 == 0 else radius // 2
        points.append([int(x + dist * np.cos(angle)), int(y - dist * np.sin(angle))])
    cv2.fillPoly(image, [np.array(points, dtype=np.int32)], color, lineType=cv2.LINE_AA)
    core = tuple(min(255, int(c * 1.3)) for c in color)
    cv2.circle(image, center, max(2, radius // 4), core, -1, lineType=cv2.LINE_AA)


STICKER_RENDERERS = {
    "sphere": draw_sphere,
    "cube": draw_cube,
    "star": draw_star,
}

STICKER_CYCLE = ("sphere", "cube", "star")
