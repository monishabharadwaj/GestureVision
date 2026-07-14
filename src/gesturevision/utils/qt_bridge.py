from __future__ import annotations

"""Convert OpenCV BGR frames to Qt images for display."""

import cv2
import numpy as np
from PyQt6.QtGui import QImage


def bgr_to_qimage(frame: np.ndarray) -> QImage:
    """
    Convert a BGR ``numpy`` array to a ``QImage``.

    A copy is made so the QImage owns its memory independently of the buffer.
    """
    if frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("Expected a BGR image with shape (H, W, 3)")

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    if not rgb.flags["C_CONTIGUOUS"]:
        rgb = np.ascontiguousarray(rgb)

    height, width, channels = rgb.shape
    bytes_per_line = channels * width
    image = QImage(
        rgb.data,
        width,
        height,
        bytes_per_line,
        QImage.Format.Format_RGB888,
    )
    return image.copy()
