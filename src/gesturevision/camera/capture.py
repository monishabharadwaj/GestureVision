from __future__ import annotations

"""OpenCV camera capture implementing the FrameSource contract."""

import logging
import os
import time
from typing import Any

import cv2

from gesturevision.core.exceptions import CameraError
from gesturevision.core.types import BGRImage, Frame

logger = logging.getLogger(__name__)

_BACKEND_MAP = {
    "default": None,
    "dshow": cv2.CAP_DSHOW,
    "msmf": cv2.CAP_MSMF,
    "v4l2": cv2.CAP_V4L2,
}

# Quiet MSMF spam when the device glitches — errors still surface via reconnect logic.
try:
    cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)
except AttributeError:
    pass


class CameraCapture:
    """Thin wrapper around ``cv2.VideoCapture`` with configurable resolution."""

    def __init__(self, config: dict[str, Any]) -> None:
        camera_cfg = config.get("camera", config)
        self._device_index = int(camera_cfg.get("device_index", 0))
        self._width = int(camera_cfg.get("width", 1280))
        self._height = int(camera_cfg.get("height", 720))
        self._fps = int(camera_cfg.get("fps", 30))
        self._backend_name = str(camera_cfg.get("backend", "default")).lower()
        self._auto_reconnect = bool(camera_cfg.get("auto_reconnect", True))
        self._reconnect_delay = float(camera_cfg.get("reconnect_delay_ms", 1000)) / 1000.0
        self._failures_before_reconnect = int(camera_cfg.get("failures_before_reconnect", 20))
        self._active_backend = self._backend_name
        self._cap: cv2.VideoCapture | None = None
        self._running = False
        self._frame_index = 0
        self._consecutive_failures = 0

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def consecutive_failures(self) -> int:
        return self._consecutive_failures

    def _backend_order(self) -> list[str]:
        """Prefer DirectShow on Windows — MSMF often loses the device mid-session."""
        preferred = self._backend_name
        if os.name != "nt":
            return [preferred]

        order: list[str] = []
        if preferred != "default":
            order.append(preferred)
        for name in ("dshow", "msmf", "default"):
            if name not in order:
                order.append(name)
        return order

    def _open_device(self, backend_name: str) -> bool:
        backend = _BACKEND_MAP.get(backend_name)
        if backend is not None:
            cap = cv2.VideoCapture(self._device_index, backend)
        else:
            cap = cv2.VideoCapture(self._device_index)

        if not cap.isOpened():
            cap.release()
            return False

        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._height)
        cap.set(cv2.CAP_PROP_FPS, self._fps)

        if self._cap is not None:
            self._cap.release()
        self._cap = cap
        self._active_backend = backend_name

        actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        logger.info(
            "Camera opened: device=%s resolution=%sx%s backend=%s",
            self._device_index,
            actual_w,
            actual_h,
            backend_name,
        )
        self._warmup()
        return True

    def _warmup(self) -> None:
        """Discard a few frames so the driver stabilizes after open."""
        if not self.is_open:
            return
        assert self._cap is not None
        for _ in range(5):
            self._cap.grab()
            time.sleep(0.02)

    def start(self) -> None:
        """Open the camera device and apply capture properties."""
        if self.is_open:
            self._running = True
            return

        last_error = ""
        for backend_name in self._backend_order():
            if self._open_device(backend_name):
                self._running = True
                self._frame_index = 0
                self._consecutive_failures = 0
                return
            last_error = backend_name

        raise CameraError(
            f"Unable to open camera device {self._device_index} "
            f"(tried backends: {', '.join(self._backend_order())}; last={last_error})"
        )

    def read(self) -> Frame | None:
        """Read a single frame from the camera."""
        ok, data = self.read_raw()
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
        grabbed = self._cap.grab()
        if not grabbed:
            self._consecutive_failures += 1
            return False, None

        ok, data = self._cap.retrieve()
        if not ok or data is None:
            self._consecutive_failures += 1
            return False, None

        self._consecutive_failures = 0
        return True, data

    def needs_reconnect(self) -> bool:
        return self._consecutive_failures >= self._failures_before_reconnect

    def reconnect(self) -> bool:
        """Release and reopen the camera — tries backend fallbacks on Windows."""
        if not self._auto_reconnect:
            return False

        logger.warning(
            "Camera lost after %d failed grabs (backend=%s) — reconnecting…",
            self._consecutive_failures,
            self._active_backend,
        )
        self._release_cap()
        time.sleep(self._reconnect_delay)

        for backend_name in self._backend_order():
            if self._open_device(backend_name):
                self._running = True
                self._consecutive_failures = 0
                logger.info("Camera reconnected with backend=%s", backend_name)
                return True

        self._running = False
        logger.error("Camera reconnect failed for device %s", self._device_index)
        return False

    def stop(self) -> None:
        """Stop capture and release the device."""
        self._running = False
        self._release_cap()

    def _release_cap(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None
            logger.info("Camera released")
