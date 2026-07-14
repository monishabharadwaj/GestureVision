from __future__ import annotations

"""Save processed frames as screenshots."""

import logging
from datetime import datetime, timezone
from pathlib import Path

import cv2

from gesturevision.core.types import BGRImage

logger = logging.getLogger(__name__)


def save_screenshot(frame: BGRImage, directory: Path) -> Path:
    """Write a timestamped PNG screenshot and return its path."""
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = directory / f"screenshot_{timestamp}.png"
    if not cv2.imwrite(str(path), frame):
        raise OSError(f"Failed to write screenshot: {path}")
    logger.info("Screenshot saved: %s", path)
    return path
