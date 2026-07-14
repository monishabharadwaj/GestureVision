from __future__ import annotations

"""Persistent picture action board — tap-free visual menu."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from gesturevision.accessibility.picture_cards import PictureCard, card_by_id


class PictureCell(QWidget):
    """One large emoji tile on the picture board."""

    def __init__(self, card: PictureCard, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._card = card
        self._active = False
        self.setMinimumSize(72, 72)

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 — Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(3, 3, -3, -3)
        bg = QColor(self._card.color if self._active else "#1a1a1a")
        painter.setBrush(bg)
        border = QColor("#ffff00" if self._active else "#ffffff")
        painter.setPen(QPen(border, 4 if self._active else 2))
        painter.drawRoundedRect(rect, 12, 12)

        font = QFont("Segoe UI Emoji", 28)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self._card.emoji)


class PictureBoardOverlay(QFrame):
    """Bottom picture menu — music, learn, paint, etc. without reading."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PictureBoardOverlay")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)

        title = QLabel("PICTURES — do the hand pose shown above")
        title.setObjectName("MutedLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self._row = QHBoxLayout()
        self._row.setSpacing(8)
        layout.addLayout(self._row)

        self._cells: dict[str, PictureCell] = {}

    def set_cards(self, card_ids: list[str]) -> None:
        while self._row.count():
            item = self._row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cells.clear()

        for card_id in card_ids:
            card = card_by_id(card_id)
            if card is None:
                continue
            cell = PictureCell(card)
            self._row.addWidget(cell, stretch=1)
            self._cells[card_id] = cell

        if self._cells:
            self.show()
            self.raise_()

    def highlight(self, card_id: str | None) -> None:
        for key, cell in self._cells.items():
            cell.set_active(key == card_id)

    def hide_board(self) -> None:
        self.hide()
