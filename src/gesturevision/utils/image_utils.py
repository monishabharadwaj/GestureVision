from __future__ import annotations

"""OpenCV drawing helpers for hand overlays."""

import cv2
import numpy as np

from gesturevision.core.types import BGRImage, HandResult
from gesturevision.hand_tracking import landmarks as lm


def draw_hand_landmarks(
    frame: BGRImage,
    hands: list[HandResult],
    *,
    connection_color: tuple[int, int, int] = (80, 200, 120),
    landmark_color: tuple[int, int, int] = (60, 180, 255),
    tip_color: tuple[int, int, int] = (100, 220, 255),
) -> BGRImage:
    """Draw hand skeletons and joint markers onto ``frame``."""
    height, width = frame.shape[:2]

    for hand in hands:
        points = hand.landmarks
        pixel_points: list[tuple[int, int]] = []
        for idx in range(lm.NUM_LANDMARKS):
            x = int(points[idx][0] * width)
            y = int(points[idx][1] * height)
            pixel_points.append((x, y))

        for start, end in lm.HAND_CONNECTIONS:
            cv2.line(frame, pixel_points[start], pixel_points[end], connection_color, 2, cv2.LINE_AA)

        for idx, point in enumerate(pixel_points):
            color = tip_color if idx in lm.FINGER_TIPS else landmark_color
            radius = 5 if idx in lm.FINGER_TIPS else 3
            cv2.circle(frame, point, radius, color, -1, cv2.LINE_AA)

    return frame


def draw_finger_cursor(
    frame: BGRImage,
    position: tuple[int, int] | None,
    *,
    color: tuple[int, int, int] = (80, 80, 255),
    radius: int = 14,
) -> BGRImage:
    """Draw a crosshair cursor at the index fingertip pixel position."""
    if position is None:
        return frame

    x, y = position
    cv2.circle(frame, (x, y), radius, color, 2, cv2.LINE_AA)
    cv2.circle(frame, (x, y), 4, color, -1, cv2.LINE_AA)
    arm = radius + 6
    cv2.line(frame, (x - arm, y), (x + arm, y), color, 2, cv2.LINE_AA)
    cv2.line(frame, (x, y - arm), (x, y + arm), color, 2, cv2.LINE_AA)
    return frame


def draw_reveal_wipe(
    frame: BGRImage,
    split_x: int,
    feather: int,
) -> BGRImage:
    """Draw the reveal divider and REAL / MOVIE labels."""
    height = frame.shape[0]
    cv2.line(frame, (split_x, 0), (split_x, height - 1), (120, 220, 255), 2, cv2.LINE_AA)
    cv2.putText(
        frame,
        "REAL",
        (max(8, split_x - 80), 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (180, 255, 180),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        frame,
        "MOVIE",
        (min(frame.shape[1] - 90, split_x + 12), 28),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (180, 180, 255),
        2,
        cv2.LINE_AA,
    )
    return frame
