from __future__ import annotations

"""Compact corner pictograph chip — does not cover camera or pose strip."""

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QWidget

from gesturevision.accessibility.picture_cards import PictureCard


# Continuous gestures must never flash a covering pictograph.
SILENT_GESTURES = frozenset({"index_finger", "pinch", "unknown", "—"})


class PictographCaptionOverlay(QWidget):
    """Small top-right chip: pose + action emoji (no reading, no fullscreen)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)
        layout.addStretch(1)

        chip = QWidget()
        chip.setObjectName("PictographChip")
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(10, 6, 10, 6)
        chip_layout.setSpacing(8)

        self._pose = QLabel("")
        self._pose.setObjectName("PictographPose")
        self._pose.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip_layout.addWidget(self._pose)

        self._emoji = QLabel("")
        self._emoji.setObjectName("PictographEmoji")
        self._emoji.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip_layout.addWidget(self._emoji)

        layout.addWidget(chip, alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_card(self, card: PictureCard, duration_ms: int = 1200) -> None:
        self._pose.setText(card.pose)
        self._emoji.setText(card.emoji)
        self.show()
        self.raise_()
        self._timer.stop()
        self._timer.start(max(duration_ms, 700))
