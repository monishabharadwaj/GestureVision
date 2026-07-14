from __future__ import annotations

"""Download and resolve MediaPipe model assets."""

import logging
import urllib.request
from pathlib import Path

from gesturevision.core.exceptions import ModelError

logger = logging.getLogger(__name__)

HAND_LANDMARKER_URL = (
    "https://storage.googleapis.com/mediapipe-models/"
    "hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"
)
HAND_LANDMARKER_FILENAME = "hand_landmarker.task"


def ensure_hand_landmarker_model(models_dir: Path) -> Path:
    """
    Return the path to the hand landmarker model, downloading it if missing.

    The model is cached under ``models_dir`` and reused on subsequent runs.
    """
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / HAND_LANDMARKER_FILENAME

    if model_path.is_file():
        logger.debug("Using cached hand landmarker model: %s", model_path)
        return model_path

    logger.info("Downloading hand landmarker model to %s", model_path)
    try:
        urllib.request.urlretrieve(HAND_LANDMARKER_URL, model_path)
    except OSError as exc:
        raise ModelError(f"Failed to download hand landmarker model: {exc}") from exc

    if not model_path.is_file():
        raise ModelError(f"Hand landmarker model missing after download: {model_path}")

    logger.info("Hand landmarker model ready")
    return model_path
