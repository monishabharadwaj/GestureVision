from __future__ import annotations

"""Large on-screen captions for Dandelion (deaf) mode."""

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class CaptionOverlay(QWidget):
    """Timed high-contrast caption banner over the video feed."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addStretch(1)

        self._label = QLabel("")
        self._label.setObjectName("CaptionBanner")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_caption(self, text: str, duration_ms: int = 4000) -> None:
        self._label.setText(text.upper())
        self.show()
        self.raise_()
        self._timer.stop()
        self._timer.start(max(duration_ms, 1000))
