from __future__ import annotations

"""Shared domain types used across the perception and effect pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray


Handedness = Literal["Left", "Right"]
QualityTier = Literal["preview", "full"]
BGRImage = NDArray[np.uint8]


class GestureType(str, Enum):
    """Recognizable hand gestures."""

    INDEX_FINGER = "index_finger"
    PEACE = "peace"
    THUMBS_UP = "thumbs_up"
    OK_SIGN = "ok_sign"
    CLOSED_FIST = "closed_fist"
    ROCK_SIGN = "rock_sign"
    PINCH = "pinch"
    UNKNOWN = "unknown"


class AppMode(str, Enum):
    """High-level application operating modes."""

    LIVE = "live"
    IMAGE_EDIT = "image_edit"
    RECORDING = "recording"
    SETTINGS = "settings"
    PAUSED = "paused"


class AccessibilityProfile(str, Enum):
    """User accessibility profiles for Beauty (blind) and Dandelion (deaf) modes."""

    STANDARD = "standard"
    BEAUTY = "beauty"
    DANDELION = "dandelion"


@dataclass(slots=True)
class Frame:
    """A single captured video frame with metadata."""

    data: BGRImage
    timestamp: float
    index: int


@dataclass(slots=True)
class HandResult:
    """Result of tracking a single hand."""

    landmarks: NDArray[np.float32]  # shape (21, 3) — normalized x, y, z
    handedness: Handedness
    confidence: float


@dataclass(slots=True)
class GestureEvent:
    """A recognized gesture at a point in time."""

    gesture: GestureType
    hand: Handedness
    confidence: float
    timestamp: float


@dataclass(slots=True)
class EffectContext:
    """Input context passed to every effect processor."""

    frame: BGRImage
    finger_position: tuple[float, float] | None = None
    pixel_position: tuple[int, int] | None = None
    active_gesture: GestureType = GestureType.UNKNOWN
    drawing: bool = False
    pinch_strength: float = 0.0
    params: dict[str, Any] = field(default_factory=dict)
    quality: QualityTier = "preview"


@dataclass(slots=True)
class PipelineMetrics:
    """Per-frame timing and throughput metrics."""

    capture_ms: float = 0.0
    tracking_ms: float = 0.0
    gesture_ms: float = 0.0
    effect_ms: float = 0.0
    total_ms: float = 0.0
    fps: float = 0.0


@dataclass(slots=True)
class ProcessedFrame:
    """Output of a single pipeline iteration ready for UI rendering."""

    image: BGRImage
    metrics: PipelineMetrics
    hands: list[HandResult]
    finger_position: tuple[float, float] | None
    active_gesture: GestureType
    gesture_confidence: float = 0.0
    pinch_strength: float = 0.0
    action_event: GestureEvent | None = None
    active_effect: str = "original"
    pixel_position: tuple[int, int] | None = None
