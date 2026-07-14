from __future__ import annotations

"""Transient toast notifications for launch errors and confirmations."""

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class ToastOverlay(QWidget):
    """Top-right toast — auto-dismiss after a few seconds."""

    _KIND_STYLES = {
        "error": "ToastError",
        "success": "ToastSuccess",
        "info": "ToastInfo",
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addStretch(1)

        self._label = QLabel("")
        self._label.setObjectName("ToastInfo")
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setWordWrap(True)
        layout.addWidget(self._label, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_toast(self, message: str, kind: str = "info", duration_ms: int = 3500) -> None:
        style = self._KIND_STYLES.get(kind, "ToastInfo")
        self._label.setObjectName(style)
        self._label.setText(message)
        self._label.style().unpolish(self._label)
        self._label.style().polish(self._label)
        self.show()
        self.raise_()
        self._timer.stop()
        self._timer.start(max(duration_ms, 1500))
