from __future__ import annotations

"""Always-visible next-step banner for Dandelion mode."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class NextStepOverlay(QWidget):
    """Top banner that tells the user exactly what gesture or voice command to try next."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 0)

        self._label = QLabel("NEXT → Press START CAMERA")
        self._label.setObjectName("NextStepBanner")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label)
        self.show()

    def set_message(self, text: str) -> None:
        self._label.setText(text)
        self.show()
        self.raise_()
