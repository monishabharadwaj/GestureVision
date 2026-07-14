from __future__ import annotations

"""Large on-screen dialogue for deaf users — agent questions and user replies."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class VisualDialogueOverlay(QWidget):
    """Shows what the app asks and what the user said — no sound required."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self._agent = QLabel("")
        self._agent.setObjectName("DialogueAgent")
        self._agent.setWordWrap(True)
        self._agent.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._agent)

        self._user = QLabel("")
        self._user.setObjectName("DialogueUser")
        self._user.setWordWrap(True)
        self._user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._user)

    def show_agent(self, text: str) -> None:
        self._agent.setText(f"APP: {text.upper()}")
        self.show()
        self.raise_()

    def show_user(self, text: str) -> None:
        self._user.setText(f'YOU SAID: "{text.upper()}"')

    def show_exchange(self, agent: str, user: str = "") -> None:
        self.show_agent(agent)
        if user:
            self.show_user(user)

    def clear_user(self) -> None:
        self._user.setText("")
