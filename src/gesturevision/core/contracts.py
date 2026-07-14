from __future__ import annotations

"""Protocol contracts that decouple infrastructure from the application core."""

from pathlib import Path
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

from gesturevision.core.types import (
    BGRImage,
    EffectContext,
    Frame,
    GestureEvent,
    HandResult,
)


@runtime_checkable
class FrameSource(Protocol):
    """Produces video frames from a camera or other input."""

    def start(self) -> None:
        """Begin capturing frames."""

    def read(self) -> Frame | None:
        """Return the latest available frame, or None if unavailable."""

    def stop(self) -> None:
        """Stop capturing and release resources."""


@runtime_checkable
class HandTracker(Protocol):
    """Detects and tracks hand landmarks in a frame."""

    def process(self, frame: BGRImage) -> list[HandResult]:
        """Return tracked hands for the given BGR frame."""


@runtime_checkable
class GestureRecognizer(Protocol):
    """Classifies hand poses into discrete gesture events."""

    def recognize(self, hands: list[HandResult]) -> list[GestureEvent]:
        """Return recognized gestures for the given hands."""


@runtime_checkable
class Effect(Protocol):
    """Transforms a frame according to an effect algorithm."""

    name: str

    def apply(self, ctx: EffectContext) -> BGRImage:
        """Apply the effect and return the processed frame."""

    def supports_realtime(self) -> bool:
        """Return True if the effect can run at interactive frame rates."""


@runtime_checkable
class AIModel(Protocol):
    """Loads and runs an AI inference model asynchronously-friendly."""

    name: str
    version: str

    def load(self, weights_path: Path) -> None:
        """Load model weights from disk."""

    def infer(self, frame: NDArray[np.uint8], **kwargs: object) -> NDArray[np.uint8]:
        """Run inference and return a processed frame."""

    def unload(self) -> None:
        """Release model resources."""

    def estimated_latency_ms(self) -> float:
        """Estimate typical inference latency in milliseconds."""
