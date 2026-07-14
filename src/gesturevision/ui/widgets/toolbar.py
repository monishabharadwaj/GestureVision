from __future__ import annotations

"""Top toolbar for camera and session controls."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget


class Toolbar(QFrame):
    """Session controls shown above the video area."""

    start_clicked = pyqtSignal()
    stop_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Toolbar")
        self.setFixedHeight(48)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 6, 16, 6)
        layout.setSpacing(8)

        title = QLabel("Live Workspace")
        title.setObjectName("StatusLabel")
        layout.addWidget(title)
        layout.addStretch(1)

        self.start_button = QPushButton("Start Camera")
        self.start_button.setObjectName("PrimaryButton")
        self.start_button.clicked.connect(self.start_clicked.emit)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_clicked.emit)
        layout.addWidget(self.stop_button)
