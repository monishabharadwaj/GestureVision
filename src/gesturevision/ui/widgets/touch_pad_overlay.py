from __future__ import annotations

"""On-screen touch bar — point your finger like a touchscreen."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class TouchPadOverlay(QFrame):
    """Large bottom buttons; finger hover highlights, pinch or hold to tap."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("TouchPadOverlay")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        title = QLabel("TOUCH BAR — point finger, hold or pinch to tap")
        title.setObjectName("MutedLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self._row = QHBoxLayout()
        self._row.setSpacing(6)
        layout.addLayout(self._row)

        self._labels: dict[str, QLabel] = {}
        self._active: str | None = None

    def set_targets(self, targets: list[tuple[str, str]]) -> None:
        """targets: list of (app_id, label)."""
        while self._row.count():
            item = self._row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._labels.clear()

        for app_id, label in targets:
            cell = QLabel(label.upper())
            cell.setObjectName("TouchCell")
            cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cell.setMinimumHeight(56)
            self._row.addWidget(cell, stretch=1)
            self._labels[app_id] = cell

        if targets:
            self.show()
            self.raise_()

    def set_hover(self, app_id: str | None) -> None:
        self._active = app_id
        for key, label in self._labels.items():
            label.setObjectName("TouchCellActive" if key == app_id else "TouchCell")
            label.style().unpolish(label)
            label.style().polish(label)

    def hide_bar(self) -> None:
        self.hide()
