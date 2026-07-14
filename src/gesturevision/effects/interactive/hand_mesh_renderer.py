from __future__ import annotations

"""Dual-hand volumetric wireframe lattice (LinkedIn-style AR mesh)."""

import math

import cv2
import numpy as np

from gesturevision.core.types import BGRImage, HandResult
from gesturevision.hand_tracking import landmarks as lm


# Landmark rings used to build the 3D "cage" between two facing hands.
_PALM_RING: tuple[int, ...] = (
    lm.WRIST,
    lm.THUMB_CMC,
    lm.INDEX_MCP,
    lm.MIDDLE_MCP,
    lm.RING_MCP,
    lm.PINKY_MCP,
)
_KNUCKLE_RING: tuple[int, ...] = (
    lm.THUMB_MCP,
    lm.INDEX_MCP,
    lm.MIDDLE_MCP,
    lm.RING_MCP,
    lm.PINKY_MCP,
)
_MID_RING: tuple[int, ...] = (
    lm.THUMB_IP,
    lm.INDEX_PIP,
    lm.MIDDLE_PIP,
    lm.RING_PIP,
    lm.PINKY_PIP,
)
_TIP_RING: tuple[int, ...] = (
    lm.THUMB_TIP,
    lm.INDEX_TIP,
    lm.MIDDLE_TIP,
    lm.RING_TIP,
    lm.PINKY_TIP,
)
_LATTICE_RINGS: tuple[tuple[int, ...], ...] = (_PALM_RING, _KNUCKLE_RING, _MID_RING, _TIP_RING)
_SUBDIVISIONS = 4  # steps between left and right hand along each bridge


def _project(
    hand: HandResult,
    width: int,
    height: int,
    index: int,
) -> tuple[int, int, float]:
    point = hand.landmarks[index]
    return int(point[0] * width), int(point[1] * height), float(point[2])


def _sort_hands_left_right(hands: list[HandResult], width: int) -> tuple[HandResult, HandResult]:
    """Order hands by wrist x so bridges draw left→right on screen."""
    if len(hands) < 2:
        raise ValueError("Need two hands for cross-hand mesh")

    def wrist_x(hand: HandResult) -> float:
        return float(hand.landmarks[lm.WRIST][0])

    return tuple(sorted(hands[:2], key=wrist_x))  # type: ignore[return-value]


def _depth_color(z: float, base: tuple[int, int, int]) -> tuple[int, int, int]:
    shift = int(z * 80)
    return (
        max(0, min(255, base[0] + shift)),
        max(0, min(255, base[1] - shift // 2)),
        max(0, min(255, base[2] + shift // 3)),
    )


def _glow_line(
    frame: BGRImage,
    start: tuple[int, int],
    end: tuple[int, int],
    color: tuple[int, int, int],
    thickness: int,
) -> None:
    cv2.line(frame, start, end, (0, 0, 0), thickness + 2, cv2.LINE_AA)
    cv2.line(frame, start, end, color, thickness, cv2.LINE_AA)


def _glow_node(frame: BGRImage, center: tuple[int, int], color: tuple[int, int, int], radius: int) -> None:
    cv2.circle(frame, center, radius + 2, (0, 0, 0), 1, cv2.LINE_AA)
    cv2.circle(frame, center, radius, color, -1, cv2.LINE_AA)
    cv2.circle(frame, center, max(1, radius // 2), (255, 255, 255), -1, cv2.LINE_AA)


def _lerp_point(
    a: tuple[int, int, float],
    b: tuple[int, int, float],
    t: float,
) -> tuple[int, int, float]:
    return (
        int(a[0] + (b[0] - a[0]) * t),
        int(a[1] + (b[1] - a[1]) * t),
        float(a[2] + (b[2] - a[2]) * t),
    )


def draw_hand_wireframe(
    frame: BGRImage,
    hand: HandResult,
    *,
    line_color: tuple[int, int, int] = (80, 200, 120),
    tip_color: tuple[int, int, int] = (0, 220, 255),
    z_scale: int = 18,
) -> None:
    """Draw a single-hand skeleton with light depth offset."""
    height, width = frame.shape[:2]
    pixels: list[tuple[int, int, float]] = [
        _project(hand, width, height, idx) for idx in range(lm.NUM_LANDMARKS)
    ]

    for start, end in lm.HAND_CONNECTIONS:
        x1, y1, z1 = pixels[start]
        x2, y2, z2 = pixels[end]
        z_avg = (z1 + z2) / 2.0
        offset = int(z_avg * z_scale)
        color = _depth_color(z_avg, line_color)
        _glow_line(
            frame,
            (x1 + offset, y1 - offset),
            (x2 + offset, y2 - offset),
            color,
            2 + int(abs(z_avg) * 3),
        )

    for tip in lm.FINGER_TIPS:
        x, y, z = pixels[tip]
        offset = int(z * z_scale)
        _glow_node(frame, (x + offset, y - offset), _depth_color(z, tip_color), 5)


def draw_cross_hand_lattice(
    frame: BGRImage,
    left: HandResult,
    right: HandResult,
    *,
    bridge_color: tuple[int, int, int] = (255, 180, 60),
    mesh_fill_alpha: float = 0.22,
) -> None:
    """
    Build a volumetric wireframe cage between both hands:

    - bridge every corresponding landmark (wrist → tips)
    - subdivide bridges into a grid
    - link neighboring fingers at each depth slice
    - fill translucent facets (glass mesh look)
    """
    height, width = frame.shape[:2]
    left_pts = [_project(left, width, height, i) for i in range(lm.NUM_LANDMARKS)]
    right_pts = [_project(right, width, height, i) for i in range(lm.NUM_LANDMARKS)]

    # 1) Direct landmark bridges (full skeleton correspondence).
    for index in range(lm.NUM_LANDMARKS):
        lx, ly, lz = left_pts[index]
        rx, ry, rz = right_pts[index]
        z_avg = (lz + rz) / 2.0
        color = _depth_color(z_avg, bridge_color)
        thickness = 1 if index not in lm.FINGER_TIPS else 2
        _glow_line(frame, (lx, ly), (rx, ry), color, thickness)

    # 2) Lattice slices along the mid-space between hands.
    overlay = frame.copy()
    fill = (180, 120, 40)

    for ring in _LATTICE_RINGS:
        slices: list[list[tuple[int, int]]] = [[] for _ in range(_SUBDIVISIONS + 1)]
        for landmark in ring:
            for step in range(_SUBDIVISIONS + 1):
                t = step / _SUBDIVISIONS
                px, py, pz = _lerp_point(left_pts[landmark], right_pts[landmark], t)
                slices[step].append((px, py))
                if 0 < step < _SUBDIVISIONS:
                    color = _depth_color(pz, (0, 200, 255))
                    _glow_node(frame, (px, py), color, 2)

        # Connect points within each depth slice (finger-to-finger).
        for step_pts in slices:
            for i in range(len(step_pts) - 1):
                _glow_line(frame, step_pts[i], step_pts[i + 1], bridge_color, 1)
            if len(step_pts) >= 3:
                _glow_line(frame, step_pts[0], step_pts[-1], bridge_color, 1)

        # Facet fills between consecutive fingers × consecutive depth steps.
        for fi in range(len(ring) - 1):
            for step in range(_SUBDIVISIONS):
                quad = np.array(
                    [
                        slices[step][fi],
                        slices[step + 1][fi],
                        slices[step + 1][fi + 1],
                        slices[step][fi + 1],
                    ],
                    dtype=np.int32,
                )
                cv2.fillConvexPoly(overlay, quad, fill)

    # 3) Diagonal accents on tip ring for extra "3D cage" look.
    tip_left = [left_pts[i][:2] for i in _TIP_RING]
    tip_right = [right_pts[i][:2] for i in _TIP_RING]
    for i in range(len(_TIP_RING) - 1):
        _glow_line(frame, tip_left[i], tip_right[i + 1], (0, 220, 255), 1)
        _glow_line(frame, tip_right[i], tip_left[i + 1], (0, 220, 255), 1)

    mid_left = tip_left[len(tip_left) // 2]
    mid_right = tip_right[len(tip_right) // 2]
    dist = math.hypot(mid_right[0] - mid_left[0], mid_right[1] - mid_left[1])
    if dist > 40:
        cx = (mid_left[0] + mid_right[0]) // 2
        cy = (mid_left[1] + mid_right[1]) // 2
        _glow_node(frame, (cx, cy), (0, 255, 255), 4)

    cv2.addWeighted(overlay, mesh_fill_alpha, frame, 1.0 - mesh_fill_alpha, 0, frame)


def draw_dual_hand_mesh(
    frame: BGRImage,
    hands: list[HandResult],
    *,
    line_color: tuple[int, int, int] = (80, 200, 120),
    tip_color: tuple[int, int, int] = (0, 220, 255),
    bridge_color: tuple[int, int, int] = (255, 180, 60),
    z_scale: int = 18,
    mesh_fill_alpha: float = 0.22,
) -> BGRImage:
    """
    Render hand skeletons plus a dense volumetric lattice when both hands appear.
    """
    if not hands:
        return frame

    for hand in hands:
        draw_hand_wireframe(
            frame,
            hand,
            line_color=line_color,
            tip_color=tip_color,
            z_scale=z_scale,
        )

    if len(hands) >= 2:
        left, right = _sort_hands_left_right(hands, frame.shape[1])
        draw_cross_hand_lattice(
            frame,
            left,
            right,
            bridge_color=bridge_color,
            mesh_fill_alpha=mesh_fill_alpha,
        )

    return frame
