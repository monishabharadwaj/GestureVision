from __future__ import annotations

"""MediaPipe Tasks Vision hand landmarker implementation."""

import logging
from pathlib import Path
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import (
    HandLandmarker,
    HandLandmarkerOptions,
    RunningMode,
)

from gesturevision.core.types import BGRImage, HandResult, Handedness
from gesturevision.hand_tracking.model_assets import ensure_hand_landmarker_model
from gesturevision.hand_tracking.smoothing import LandmarkSmoother

logger = logging.getLogger(__name__)


class MediaPipeHandTracker:
    """Detects and tracks up to two hands using MediaPipe HandLandmarker."""

    def __init__(
        self,
        config: dict[str, Any],
        models_dir: Path,
    ) -> None:
        tracking_cfg = config.get("hand_tracking", config)
        self._max_num_hands = int(tracking_cfg.get("max_num_hands", 2))
        self._min_detection = float(tracking_cfg.get("min_detection_confidence", 0.6))
        self._min_tracking = float(tracking_cfg.get("min_tracking_confidence", 0.5))
        self._min_presence = float(tracking_cfg.get("min_hand_presence_confidence", 0.5))

        resolution = tracking_cfg.get("tracking_resolution", {})
        self._track_width = int(resolution.get("width", 640))
        self._track_height = int(resolution.get("height", 480))

        smoothing_cfg = tracking_cfg.get("smoothing", {})
        self._smoothing_enabled = bool(smoothing_cfg.get("enabled", True))
        self._smoother = LandmarkSmoother(alpha=float(smoothing_cfg.get("alpha", 0.4)))

        model_path = ensure_hand_landmarker_model(models_dir)
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path)),
            running_mode=RunningMode.IMAGE,
            num_hands=self._max_num_hands,
            min_hand_detection_confidence=self._min_detection,
            min_hand_presence_confidence=self._min_presence,
            min_tracking_confidence=self._min_tracking,
        )
        self._landmarker = HandLandmarker.create_from_options(options)
        logger.info("MediaPipe HandLandmarker initialized")

    def close(self) -> None:
        """Release MediaPipe resources."""
        if getattr(self, "_landmarker", None) is not None:
            self._landmarker.close()
        self._landmarker = None
        self._smoother.reset()

    def process(self, frame: BGRImage) -> list[HandResult]:
        """Detect hands in a BGR frame and return normalized landmark results."""
        if frame.size == 0:
            return []

        resized = cv2.resize(frame, (self._track_width, self._track_height))
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        if not rgb.flags["C_CONTIGUOUS"]:
            rgb = np.ascontiguousarray(rgb)

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect(mp_image)

        hands: list[HandResult] = []
        if not result.hand_landmarks:
            return hands

        for landmarks, handedness_list in zip(
            result.hand_landmarks,
            result.handedness,
            strict=False,
        ):
            label = handedness_list[0].category_name
            handedness: Handedness = "Right" if label == "Right" else "Left"
            confidence = float(handedness_list[0].score)

            points = np.array(
                [[lm.x, lm.y, lm.z] for lm in landmarks],
                dtype=np.float32,
            )
            hands.append(
                HandResult(
                    landmarks=points,
                    handedness=handedness,
                    confidence=confidence,
                )
            )

        if self._smoothing_enabled and hands:
            return self._smoother.smooth(hands)
        return hands
