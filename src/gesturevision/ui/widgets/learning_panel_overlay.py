from __future__ import annotations

"""Scrollable learning text for deaf users who cannot hear explanations."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget


class LearningPanelOverlay(QWidget):
    """Shows a full readable explanation on screen — stays until dismissed."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._title = QLabel("HERE IS WHAT I FOUND")
        self._title.setObjectName("LearningTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._title)

        self._topic = QLabel("")
        self._topic.setObjectName("LearningTopic")
        self._topic.setWordWrap(True)
        self._topic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._topic)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setObjectName("LearningScroll")

        self._body = QLabel("")
        self._body.setObjectName("LearningBody")
        self._body.setWordWrap(True)
        self._body.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        scroll.setWidget(self._body)
        layout.addWidget(scroll, stretch=1)

        self._footer = QLabel("READ ABOVE — Peace sign to learn something else")
        self._footer.setObjectName("LearningFooter")
        self._footer.setWordWrap(True)
        self._footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._footer)

    def show_lesson(self, topic: str, explanation: str) -> None:
        self._topic.setText(f"TOPIC: {topic.upper()}")
        self._body.setText(explanation.strip())
        self.show()
        self.raise_()

    def hide_lesson(self) -> None:
        self.hide()
