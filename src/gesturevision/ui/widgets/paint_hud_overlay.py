from __future__ import annotations

"""Small paint-studio status bar — shows brush/filter without blocking the camera."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PaintHudOverlay(QWidget):
    """Bottom status strip for Dandelion paint mode."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 10)
        layout.setSpacing(4)

        self._status = QLabel("PAINT STUDIO — show ☝ index finger to draw on your face")
        self._status.setObjectName("PaintHudStatus")
        self._status.setWordWrap(True)
        self._status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._status)

        self._detail = QLabel("Brush: Neon  |  Background: Live camera")
        self._detail.setObjectName("PaintHudDetail")
        self._detail.setWordWrap(True)
        self._detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._detail)

    def show_status(self, message: str, *, brush: str = "", background: str = "") -> None:
        self._status.setText(message)
        if brush or background:
            parts = []
            if brush:
                parts.append(f"Brush: {brush}")
            if background:
                parts.append(f"Background: {background}")
            self._detail.setText("  |  ".join(parts))
        self.show()
        self.raise_()

    def set_detail(self, brush: str, background: str) -> None:
        self._detail.setText(f"Brush: {brush}  |  Background: {background}")
