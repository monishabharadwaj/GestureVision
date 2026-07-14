from __future__ import annotations

"""Brief on-screen gesture label when an action fires."""

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class GestureFlashOverlay(QWidget):
    """Large centered gesture name — flashes on action trigger."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addStretch(2)

        self._gesture = QLabel("")
        self._gesture.setObjectName("GestureFlashName")
        self._gesture.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._gesture)

        self._action = QLabel("")
        self._action.setObjectName("GestureFlashAction")
        self._action.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._action)

        layout.addStretch(3)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def flash(self, gesture_name: str, action_label: str = "", duration_ms: int = 1400) -> None:
        self._gesture.setText(gesture_name.upper())
        if action_label:
            self._action.setText(action_label)
            self._action.show()
        else:
            self._action.hide()
        self.show()
        self.raise_()
        self._timer.stop()
        self._timer.start(max(duration_ms, 800))
