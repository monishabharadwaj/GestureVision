from __future__ import annotations

"""Per-frame perception pipeline: mirror → track → effect → overlay."""

import logging
import time
from typing import Any

import cv2

from gesturevision.core.contracts import HandTracker
from gesturevision.core.types import Frame, GestureType, PipelineMetrics, ProcessedFrame
from gesturevision.effects.engine import EffectEngine
from gesturevision.gesture_recognition.recognizer import GestureRecognizer
from gesturevision.input.finger_controller import FingerController
from gesturevision.performance.fps_counter import FpsCounter
from gesturevision.core.types import GestureType
from gesturevision.effects.interactive.image_reveal import ImageRevealEffect
from gesturevision.utils.image_utils import (
    draw_finger_cursor,
    draw_hand_landmarks,
    draw_reveal_wipe,
)

logger = logging.getLogger(__name__)


class FramePipeline:
    """Processes captured frames through tracking, effects, gestures, and overlays."""

    def __init__(
        self,
        hand_tracker: HandTracker,
        finger_controller: FingerController,
        gesture_recognizer: GestureRecognizer,
        effect_engine: EffectEngine,
        *,
        mirror_preview: bool = True,
        fps_counter: FpsCounter | None = None,
    ) -> None:
        self._tracker = hand_tracker
        self._finger_controller = finger_controller
        self._gesture_recognizer = gesture_recognizer
        self._effect_engine = effect_engine
        self._mirror_preview = mirror_preview
        self._fps_counter = fps_counter or FpsCounter()
        self._last_capture_timestamp = 0.0

    @property
    def effect_engine(self) -> EffectEngine:
        return self._effect_engine

    @property
    def mirror_preview(self) -> bool:
        return self._mirror_preview

    def set_mirror_preview(self, enabled: bool) -> None:
        self._mirror_preview = enabled
        # Frame is mirrored before tracking — landmarks are already in display space.
        self._finger_controller.set_mirror(not enabled)

    def process(self, frame: Frame) -> ProcessedFrame | None:
        """Run one pipeline iteration and return a render-ready frame."""
        loop_start = time.perf_counter()
        image = frame.data

        if self._mirror_preview:
            image = cv2.flip(image, 1)

        capture_ms = 0.0
        if self._last_capture_timestamp > 0.0:
            capture_ms = (frame.timestamp - self._last_capture_timestamp) * 1000.0
        self._last_capture_timestamp = frame.timestamp

        track_start = time.perf_counter()
        hands = self._tracker.process(image)
        tracking_ms = (time.perf_counter() - track_start) * 1000.0

        gesture_start = time.perf_counter()
        finger_position = self._finger_controller.update(hands)
        debounce_result, pinch_strength = self._gesture_recognizer.recognize(hands)
        gesture_ms = (time.perf_counter() - gesture_start) * 1000.0

        pixel_cursor = self._finger_controller.pixel_position(
            image.shape[1],
            image.shape[0],
        )

        effect_start = time.perf_counter()
        effected = self._effect_engine.apply(
            image,
            finger_position=finger_position,
            pixel_position=pixel_cursor,
            active_gesture=debounce_result.display_gesture,
            pinch_strength=pinch_strength,
        )
        effect_ms = (time.perf_counter() - effect_start) * 1000.0

        output = effected.copy()
        if hands:
            draw_hand_landmarks(output, hands)
        if debounce_result.display_gesture in (
            GestureType.INDEX_FINGER,
            GestureType.UNKNOWN,
        ) or self._effect_engine.active_effect in {"brush", "reveal"}:
            cursor_color = (255, 120, 255) if self._effect_engine.active_effect == "brush" else (120, 220, 255)
            draw_finger_cursor(output, pixel_cursor, color=cursor_color)

        if self._effect_engine.active_effect == "reveal":
            reveal = self._effect_engine.get_effect("reveal")
            if isinstance(reveal, ImageRevealEffect):
                draw_reveal_wipe(output, reveal.last_split_x, reveal.last_feather)

        total_ms = (time.perf_counter() - loop_start) * 1000.0
        fps = self._fps_counter.tick(time.perf_counter())

        metrics = PipelineMetrics(
            capture_ms=capture_ms,
            tracking_ms=tracking_ms,
            gesture_ms=gesture_ms,
            effect_ms=effect_ms,
            total_ms=total_ms,
            fps=fps,
        )

        return ProcessedFrame(
            image=output,
            metrics=metrics,
            hands=hands,
            finger_position=finger_position,
            active_gesture=debounce_result.display_gesture,
            pinch_strength=pinch_strength,
            action_event=debounce_result.action_event,
            active_effect=self._effect_engine.active_effect,
            pixel_position=pixel_cursor,
        )


def build_finger_controller(gesture_config: dict[str, Any], mirror_preview: bool) -> FingerController:
    """Create a finger controller from gesture configuration."""
    gestures_cfg = gesture_config.get("gestures", gesture_config)
    dominant = str(gestures_cfg.get("dominant_hand", "Right"))
    # When the pipeline mirrors the frame first, landmarks are already in display space.
    return FingerController(dominant_hand=dominant, mirror=not mirror_preview)


def build_gesture_recognizer(gesture_config: dict[str, Any]) -> GestureRecognizer:
    """Create a gesture recognizer from configuration."""
    return GestureRecognizer(gesture_config)
