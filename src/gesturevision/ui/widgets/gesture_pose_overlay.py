from __future__ import annotations

"""ASL-style hand-pose reference strip — shows how to shape each gesture."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QPen
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from gesturevision.accessibility.picture_cards import PictureCard


class PoseCell(QWidget):
    """Pose emoji + action emoji pair."""

    def __init__(self, card: PictureCard, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._card = card
        self._active = False
        self.setMinimumHeight(64)

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self.update()

    def paintEvent(self, event) -> None:  # noqa: N802 — Qt naming
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(2, 2, -2, -2)
        bg = QColor(self._card.color if self._active else "#111111")
        painter.setBrush(bg)
        border = QColor("#00ccff" if self._active else "#666666")
        painter.setPen(QPen(border, 3 if self._active else 1))
        painter.drawRoundedRect(rect, 8, 8)

        emoji_font = QFont("Segoe UI Emoji", 20)
        painter.setFont(emoji_font)
        top = rect.adjusted(0, 4, 0, -rect.height() // 2)
        bottom = rect.adjusted(0, rect.height() // 2, 0, -4)
        painter.drawText(top, Qt.AlignmentFlag.AlignCenter, self._card.pose)
        painter.drawText(bottom, Qt.AlignmentFlag.AlignCenter, self._card.emoji)


class GesturePoseOverlay(QFrame):
    """Top strip: hand shape → what it does (picture-only)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GesturePoseOverlay")
        self.hide()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(4)

        hint = QLabel("POSE →")
        hint.setObjectName("MutedLabel")
        layout.addWidget(hint)

        self._row = QHBoxLayout()
        self._row.setSpacing(4)
        layout.addLayout(self._row, stretch=1)

        self._cells: list[PoseCell] = []

    def set_poses(self, cards: tuple[PictureCard, ...]) -> None:
        while self._row.count():
            item = self._row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cells.clear()

        for card in cards:
            cell = PoseCell(card)
            self._row.addWidget(cell, stretch=1)
            self._cells.append(cell)

        if self._cells:
            self.show()
            self.raise_()

    def highlight_gesture(self, gesture: str | None) -> None:
        from gesturevision.accessibility.picture_cards import card_for_gesture

        active_card = card_for_gesture(gesture) if gesture else None
        for cell in self._cells:
            cell.set_active(active_card is not None and cell._card.card_id == active_card.card_id)

    def hide_panel(self) -> None:
        self.hide()
