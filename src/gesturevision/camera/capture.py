from __future__ import annotations

"""OpenCV camera capture implementing the FrameSource contract."""

import logging
from typing import Any

import cv2

import time

from gesturevision.core.exceptions import CameraError
from gesturevision.core.types import BGRImage, Frame

logger = logging.getLogger(__name__)

_BACKEND_MAP = {
    "default": None,
    "dshow": cv2.CAP_DSHOW,
    "msmf": cv2.CAP_MSMF,
    "v4l2": cv2.CAP_V4L2,
}


class CameraCapture:
    """Thin wrapper around ``cv2.VideoCapture`` with configurable resolution."""

    def __init__(self, config: dict[str, Any]) -> None:
        camera_cfg = config.get("camera", config)
        self._device_index = int(camera_cfg.get("device_index", 0))
        self._width = int(camera_cfg.get("width", 1280))
        self._height = int(camera_cfg.get("height", 720))
        self._fps = int(camera_cfg.get("fps", 30))
        self._backend_name = str(camera_cfg.get("backend", "default")).lower()
        self._cap: cv2.VideoCapture | None = None
        self._running = False
        self._frame_index = 0

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Open the camera device and apply capture properties."""
        if self.is_open:
            self._running = True
            return

        backend = _BACKEND_MAP.get(self._backend_name)
        if backend is not None:
            self._cap = cv2.VideoCapture(self._device_index, backend)
        else:
            self._cap = cv2.VideoCapture(self._device_index)

        if not self._cap.isOpened():
            raise CameraError(
                f"Unable to open camera device {self._device_index} "
                f"(backend={self._backend_name})"
            )

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        self._cap.set(cv2.CAP_PROP_FPS, self._fps)

        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(
            "Camera opened: device=%s resolution=%sx%s backend=%s",
            self._device_index,
            actual_w,
            actual_h,
            self._backend_name,
        )
        self._running = True
        self._frame_index = 0

    def read(self) -> Frame | None:
        """Read a single frame from the camera."""
        if not self.is_open:
            return None

        assert self._cap is not None
        ok, data = self._cap.read()
        if not ok or data is None:
            return None

        frame = Frame(
            data=data,
            timestamp=time.perf_counter(),
            index=self._frame_index,
        )
        self._frame_index += 1
        return frame

    def read_raw(self) -> tuple[bool, BGRImage | None]:
        """Return the raw OpenCV read tuple for the capture thread."""
        if not self.is_open:
            return False, None
        assert self._cap is not None
        return self._cap.read()

    def stop(self) -> None:
        """Stop capture and release the device."""
        self._running = False
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Camera released")
