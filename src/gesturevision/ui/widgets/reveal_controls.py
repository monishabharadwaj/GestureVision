from __future__ import annotations

"""Reveal filter selector for the sidebar."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QFrame, QLabel, QVBoxLayout, QWidget


class RevealControls(QFrame):
    """Choose which cinematic filter sits behind the reveal wipe."""

    reveal_filter_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel("FILTER BEHIND REVEAL")
        label.setObjectName("MutedLabel")
        layout.addWidget(label)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Sketch", "Edge", "Blur"])
        self.filter_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.filter_combo)

        hint = QLabel("Move finger ↔ to wipe away\nfilter and reveal real camera.")
        hint.setObjectName("MutedLabel")
        hint.setWordWrap(True)
        layout.addWidget(hint)

    def _on_filter_changed(self, label: str) -> None:
        self.reveal_filter_changed.emit(label.lower())
