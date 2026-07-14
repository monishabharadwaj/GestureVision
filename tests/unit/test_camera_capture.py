from __future__ import annotations

"""Unit tests for camera backend selection and failure tracking."""

import os

from gesturevision.camera.capture import CameraCapture


def test_windows_backend_order_prefers_dshow() -> None:
    camera = CameraCapture(
        {
            "backend": "default",
            "auto_reconnect": True,
            "reconnect_delay_ms": 500,
            "failures_before_reconnect": 10,
        }
    )
    order = camera._backend_order()
    if os.name == "nt":
        assert order[0] == "dshow"
        assert "msmf" in order
    else:
        assert order == ["default"]


def test_needs_reconnect_after_threshold() -> None:
    camera = CameraCapture({"failures_before_reconnect": 3})
    camera._consecutive_failures = 2
    assert not camera.needs_reconnect()
    camera._consecutive_failures = 3
    assert camera.needs_reconnect()
