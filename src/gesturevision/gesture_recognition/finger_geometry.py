from __future__ import annotations

"""Shared finger geometry helpers for gesture rules."""

import numpy as np
from numpy.typing import NDArray

from gesturevision.core.types import HandResult
from gesturevision.hand_tracking import landmarks as lm


def is_finger_extended(landmarks: NDArray[np.float32], tip: int, pip: int) -> bool:
    """True when the fingertip is above its PIP joint (image y-axis)."""
    return float(landmarks[tip][1]) < float(landmarks[pip][1])


def is_finger_curled(landmarks: NDArray[np.float32], tip: int, pip: int) -> bool:
    return not is_finger_extended(landmarks, tip, pip)


def fingertip_distance(landmarks: NDArray[np.float32], a: int, b: int) -> float:
    """Euclidean distance between two landmarks in normalized space."""
    ax, ay = float(landmarks[a][0]), float(landmarks[a][1])
    bx, by = float(landmarks[b][0]), float(landmarks[b][1])
    return float(np.hypot(ax - bx, ay - by))


def thumb_extended(landmarks: NDArray[np.float32]) -> bool:
    """Thumb extended outward (tip farther from wrist than IP joint)."""
    wrist = landmarks[lm.WRIST]
    tip = landmarks[lm.THUMB_TIP]
    ip = landmarks[lm.THUMB_IP]
    tip_dist = np.hypot(tip[0] - wrist[0], tip[1] - wrist[1])
    ip_dist = np.hypot(ip[0] - wrist[0], ip[1] - wrist[1])
    return float(tip_dist) > float(ip_dist) + 0.02


def thumb_up_pose(landmarks: NDArray[np.float32]) -> bool:
    """Thumb pointing up with other fingers curled."""
    thumb_up = float(landmarks[lm.THUMB_TIP][1]) < float(landmarks[lm.THUMB_IP][1])
    others_curled = all(
        is_finger_curled(landmarks, tip, pip)
        for tip, pip in (
            (lm.INDEX_TIP, lm.INDEX_PIP),
            (lm.MIDDLE_TIP, lm.MIDDLE_PIP),
            (lm.RING_TIP, lm.RING_PIP),
            (lm.PINKY_TIP, lm.PINKY_PIP),
        )
    )
    return thumb_up and others_curled


def all_fingers_curled(landmarks: NDArray[np.float32]) -> bool:
    return all(
        is_finger_curled(landmarks, tip, pip)
        for tip, pip in (
            (lm.INDEX_TIP, lm.INDEX_PIP),
            (lm.MIDDLE_TIP, lm.MIDDLE_PIP),
            (lm.RING_TIP, lm.RING_PIP),
            (lm.PINKY_TIP, lm.PINKY_PIP),
        )
    )


def pinch_strength(landmarks: NDArray[np.float32]) -> float:
    """
    Return pinch strength in [0, 1].

    1.0 means fingertips touching; 0.0 means far apart.
    """
    distance = fingertip_distance(landmarks, lm.THUMB_TIP, lm.INDEX_TIP)
    return max(0.0, min(1.0, 1.0 - (distance / 0.12)))
