from __future__ import annotations

"""On-screen navigation menu for Dandelion mode."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class GestureMenuOverlay(QFrame):
    """Large visual menu — peace for next, thumbs up to open."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("GestureMenuOverlay")
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        title = QLabel("NAVIGATION MENU")
        title.setObjectName("CaptionBanner")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self._hint = QLabel("✌ Peace = next   👍 Thumbs up = open   ✊ Fist = close")
        self._hint.setObjectName("MutedLabel")
        self._hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._hint.setWordWrap(True)
        layout.addWidget(self._hint)

        self._items_layout = QVBoxLayout()
        layout.addLayout(self._items_layout)

        self._item_labels: list[QLabel] = []

    def show_menu(self, labels: list[str], active_index: int) -> None:
        while self._items_layout.count():
            item = self._items_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._item_labels.clear()

        for index, label in enumerate(labels):
            row = QLabel(label.upper())
            row.setObjectName("CaptionBanner" if index == active_index else "MutedLabel")
            row.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._items_layout.addWidget(row)
            self._item_labels.append(row)

        self.show()
        self.raise_()

    def update_selection(self, active_index: int) -> None:
        for index, label in enumerate(self._item_labels):
            label.setObjectName("CaptionBanner" if index == active_index else "MutedLabel")
            label.style().unpolish(label)
            label.style().polish(label)

    def hide_menu(self) -> None:
        self.hide()
