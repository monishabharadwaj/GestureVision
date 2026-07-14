from __future__ import annotations

"""Status bar showing mode, effect, gesture, and FPS."""

from PyQt6.QtWidgets import QLabel, QStatusBar, QWidget


class AppStatusBar(QStatusBar):
    """Footer status indicators for runtime telemetry."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setSizeGripEnabled(False)

        self._status = QLabel("Ready")
        self._status.setObjectName("StatusLabel")
        self.addWidget(self._status, stretch=1)

        self._mode = QLabel("Mode: live")
        self._mode.setObjectName("StatusLabel")
        self.addPermanentWidget(self._mode)

        self._effect = QLabel("Effect: —")
        self._effect.setObjectName("StatusLabel")
        self.addPermanentWidget(self._effect)

        self._gesture = QLabel("Gesture: —")
        self._gesture.setObjectName("StatusLabel")
        self.addPermanentWidget(self._gesture)

        self._fps = QLabel("FPS: —")
        self._fps.setObjectName("StatusLabel")
        self.addPermanentWidget(self._fps)

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def set_mode(self, mode: str) -> None:
        self._mode.setText(f"Mode: {mode}")

    def set_effect(self, effect: str) -> None:
        self._effect.setText(f"Effect: {effect}")

    def set_gesture(self, gesture: str) -> None:
        self._gesture.setText(f"Gesture: {gesture}")

    def set_fps(self, fps: float) -> None:
        if fps <= 0:
            self._fps.setText("FPS: —")
        else:
            self._fps.setText(f"FPS: {fps:.1f}")
