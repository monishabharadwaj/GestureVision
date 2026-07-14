from __future__ import annotations

"""Domain exceptions for GestureVision AI."""


class GestureVisionError(Exception):
    """Base exception for all GestureVision errors."""


class ConfigError(GestureVisionError):
    """Raised when configuration is missing, invalid, or unreadable."""


class CameraError(GestureVisionError):
    """Raised when the camera cannot be opened or read."""


class TrackingError(GestureVisionError):
    """Raised when hand tracking fails in a non-recoverable way."""


class EffectError(GestureVisionError):
    """Raised when an effect cannot be applied or is misconfigured."""


class ModelError(GestureVisionError):
    """Raised when an AI model fails to load or run inference."""
