from __future__ import annotations

"""On-screen touch bar — point your finger like a touchscreen."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget


class TouchCellWidget(QWidget):
    """Single touch-bar button with animated dwell progress ring."""

    def __init__(self, label_text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._label_text = label_text
        self._active = False
        self._progress = 0.0
        self.setMinimumHeight(56)

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def set_progress(self, progress: float) -> None:
        clamped = max(0.0, min(1.0, progress))
        if abs(self._progress - clamped) > 0.02 or clamped in {0.0, 1.0}:
            self._progress = clamped
            self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 — Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(4, 4, -4, -4)
        bg = QColor("#ffff00") if self._active else QColor("#222222")
        fg = QColor("#000000") if self._active else QColor("#ffffff")
        border = QColor("#ffffff")

        painter.setBrush(bg)
        painter.setPen(QPen(border, 3 if self._active else 2))
        painter.drawRoundedRect(rect, 8, 8)

        if self._progress > 0.0:
            ring_rect = rect.adjusted(6, 6, -6, -6)
            span = int(360 * 16 * self._progress)
            ring_color = QColor("#00ccff") if not self._active else QColor("#0066ff")
            painter.setPen(QPen(ring_color, 5))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            start_angle = 90 * 16
            painter.drawArc(ring_rect, start_angle, -span)

        font = QFont("Segoe UI", 11, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(fg)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._label_text.upper())


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

        self._cells: dict[str, TouchCellWidget] = {}
        self._active: str | None = None

    def set_targets(self, targets: list[tuple[str, str]]) -> None:
        """targets: list of (app_id, label)."""
        while self._row.count():
            item = self._row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cells.clear()

        for app_id, label in targets:
            cell = TouchCellWidget(label)
            self._row.addWidget(cell, stretch=1)
            self._cells[app_id] = cell

        if targets:
            self.show()
            self.raise_()

    def set_hover(self, app_id: str | None, progress: float = 0.0) -> None:
        self._active = app_id
        for key, cell in self._cells.items():
            cell.set_active(key == app_id)
            cell.set_progress(progress if key == app_id else 0.0)

    def hide_bar(self) -> None:
        self.hide()
