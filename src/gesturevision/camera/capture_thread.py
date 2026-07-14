from __future__ import annotations

"""Background thread that continuously captures frames into a ring buffer."""

import logging
import threading
import time

from gesturevision.camera.capture import CameraCapture
from gesturevision.core.frame_buffer import RingBuffer
from gesturevision.core.types import Frame

logger = logging.getLogger(__name__)


class CaptureThread(threading.Thread):
    """Producer thread that writes the latest camera frames to a ring buffer."""

    def __init__(
        self,
        camera: CameraCapture,
        buffer: RingBuffer[Frame],
        stop_event: threading.Event,
    ) -> None:
        super().__init__(name="CaptureThread", daemon=True)
        self._camera = camera
        self._buffer = buffer
        self._stop_event = stop_event
        self._frame_index = 0
        self._local_failures = 0

    def run(self) -> None:
        logger.info("Capture thread started")
        while not self._stop_event.is_set():
            ok, data = self._camera.read_raw()
            if not ok or data is None:
                self._local_failures += 1
                if self._camera.needs_reconnect():
                    if not self._camera.reconnect():
                        time.sleep(0.5)
                    self._local_failures = 0
                else:
                    # Back off so OpenCV does not flood the console with MSMF warnings.
                    delay = min(0.2, 0.01 * self._local_failures)
                    time.sleep(delay)
                continue

            self._local_failures = 0
            frame = Frame(
                data=data,
                timestamp=time.perf_counter(),
                index=self._frame_index,
            )
            self._frame_index += 1
            self._buffer.push(frame)

        logger.info("Capture thread stopped")
