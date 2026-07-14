from __future__ import annotations

"""Brush type and color controls for the sidebar."""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog,
    QComboBox,
    QFrame,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from gesturevision.effects.interactive.brush_renderers import BRUSH_COLOR_PRESETS


class BrushControls(QFrame):
    """Brush style and color picker shown when Brush mode is active."""

    brush_type_changed = pyqtSignal(str)
    brush_color_changed = pyqtSignal(int, int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        type_label = QLabel("BRUSH TYPE")
        type_label.setObjectName("MutedLabel")
        layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["Neon Glow", "Soft Paint", "3D Tube", "Sparkle"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        layout.addWidget(self.type_combo)

        color_label = QLabel("COLOR")
        color_label.setObjectName("MutedLabel")
        layout.addWidget(color_label)

        grid = QGridLayout()
        grid.setSpacing(4)
        self._color_buttons: list[QPushButton] = []
        preset_items = list(BRUSH_COLOR_PRESETS.items())
        for index, (name, bgr) in enumerate(preset_items):
            btn = QPushButton()
            btn.setFixedSize(28, 28)
            btn.setToolTip(name.replace("_", " ").title())
            btn.setStyleSheet(
                f"background-color: rgb({bgr[2]}, {bgr[1]}, {bgr[0]});"
                "border: 1px solid #555; border-radius: 4px;"
            )
            btn.clicked.connect(lambda _checked, c=bgr: self._emit_color(c))
            self._color_buttons.append(btn)
            grid.addWidget(btn, index // 3, index % 3)
        layout.addLayout(grid)

        self.custom_button = QPushButton("Pick Custom Color…")
        self.custom_button.clicked.connect(self._pick_custom_color)
        layout.addWidget(self.custom_button)

    def _on_type_changed(self, label: str) -> None:
        mapping = {
            "Neon Glow": "neon",
            "Soft Paint": "soft",
            "3D Tube": "tube3d",
            "Sparkle": "sparkle",
        }
        self.brush_type_changed.emit(mapping.get(label, "neon"))

    def _emit_color(self, bgr: tuple[int, int, int]) -> None:
        self.brush_color_changed.emit(bgr[0], bgr[1], bgr[2])

    def _pick_custom_color(self) -> None:
        color = QColorDialog.getColor(QColor(255, 80, 255), self, "Choose Brush Color")
        if color.isValid():
            self.brush_color_changed.emit(color.blue(), color.green(), color.red())
