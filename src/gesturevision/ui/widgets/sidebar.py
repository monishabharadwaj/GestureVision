from __future__ import annotations

"""Left sidebar for brand, effects list, and navigation."""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFrame, QLabel, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from gesturevision.ui.widgets.brush_controls import BrushControls
from gesturevision.ui.widgets.reveal_controls import RevealControls


EFFECT_ITEMS: tuple[tuple[str, str] | tuple[None, None], ...] = (
    ("Original", "original"),
    ("Sketch", "sketch"),
    ("Blur", "blur"),
    ("Edge", "edge"),
    (None, None),
    ("Brush", "brush"),
    ("Reveal", "reveal"),
)

GESTURE_HINTS = (
    "☝ Index — paint / move wipe",
    "✌ Peace — sketch",
    "🤏 Pinch — brush/reveal size",
    "👍 Thumbs up — screenshot",
    "✊ Fist — pause",
    "👌 OK — original",
    "🤘 Rock — edge",
)


BEAUTY_HINTS = (
    "👂 Audio-only — you hear every action",
    "👍 Thumbs up — save photo",
    "✊ Fist — pause / resume",
    "🤘 Rock — music",
    "✌ Peace — hear help",
    "👌 OK — hear status",
)

DANDELION_LIVE_HINTS = (
    "PICTURE MODE — icons + hand poses, no reading",
    "🤘 Rock = 🎵 music",
    "✌ Peace = 📚 learn",
    "👌 OK = 💬 ask",
    "👍 Thumbs up = 🎨 paint",
    "☝ Index = 👆 touch bar",
    "🙌 Two hands = 3D mesh",
    "👊 Fist = 🔙 back to live",
)

DANDELION_PAINT_HINTS = (
    "PAINT — ❌ CROSS FINGERS (X) anytime to EXIT",
    "☝ Index = Draw on your face",
    "👌 OK = Next brush",
    "🤘 Rock = Next ink color",
    "✌ Peace = Next background",
    "👍 Thumbs up = Place 3D object",
    "🤏 Pinch = Brush size",
    "✊ Fist = Clear canvas",
)


class Sidebar(QFrame):
    """Navigation sidebar with effect selection and gesture hints."""

    effect_selected = pyqtSignal(str)
    brush_type_changed = pyqtSignal(str)
    brush_color_changed = pyqtSignal(int, int, int)
    reveal_filter_changed = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(280)
        self._block_signals = False
        self._effect_lookup = {
            internal: display for display, internal in EFFECT_ITEMS if internal is not None
        }

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 16, 12, 16)
        layout.setSpacing(10)

        brand = QLabel("GestureVision")
        brand.setObjectName("BrandLabel")
        layout.addWidget(brand)

        phase = QLabel("AI  ·  Phase 8")
        phase.setObjectName("PhaseBadge")
        layout.addWidget(phase)

        self.profile_label = QLabel("")
        self.profile_label.setObjectName("PhaseBadge")
        self.profile_label.hide()
        layout.addWidget(self.profile_label)

        section = QLabel("EFFECTS")
        section.setObjectName("MutedLabel")
        layout.addWidget(section)

        self.effects_list = QListWidget()
        for display, internal in EFFECT_ITEMS:
            if display is None:
                separator = QListWidgetItem("— Interactive —")
                separator.setFlags(Qt.ItemFlag.NoItemFlags)
                self.effects_list.addItem(separator)
                continue
            QListWidgetItem(display, self.effects_list)

        self.effects_list.setCurrentRow(0)
        self.effects_list.currentTextChanged.connect(self._on_effect_changed)
        layout.addWidget(self.effects_list)

        self.brush_controls = BrushControls(self)
        self.brush_controls.hide()
        self.brush_controls.brush_type_changed.connect(self.brush_type_changed.emit)
        self.brush_controls.brush_color_changed.connect(self.brush_color_changed.emit)
        layout.addWidget(self.brush_controls)

        self.reveal_controls = RevealControls(self)
        self.reveal_controls.hide()
        self.reveal_controls.reveal_filter_changed.connect(self.reveal_filter_changed.emit)
        layout.addWidget(self.reveal_controls)

        gestures = QLabel("GESTURES")
        gestures.setObjectName("MutedLabel")
        layout.addWidget(gestures)

        self._gesture_labels: list[QLabel] = []
        for hint in GESTURE_HINTS:
            label = QLabel(hint)
            label.setObjectName("MutedLabel")
            self._gesture_labels.append(label)
            layout.addWidget(label)

        layout.addStretch(1)

    def apply_accessibility_mode(
        self,
        *,
        profile_name: str,
        simplified: bool,
        reduced_effects: list[str] | None = None,
        audio_only: bool = False,
        is_dandelion: bool = False,
    ) -> None:
        """Switch between audio-only, visual paint, and full effect menus."""
        self.profile_label.setText(f"Mode: {profile_name}")
        self.profile_label.setVisible(True)

        allowed = {name.lower() for name in (reduced_effects or [])}
        self._block_signals = True
        self.effects_list.clear()

        if audio_only:
            item = QListWidgetItem("Audio navigation — no painting")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.effects_list.addItem(item)
            hints = BEAUTY_HINTS
        elif simplified and allowed:
            for display, internal in EFFECT_ITEMS:
                if internal is None:
                    continue
                if internal in allowed:
                    QListWidgetItem(display, self.effects_list)
            self.effects_list.setCurrentRow(0)
            hints = DANDELION_LIVE_HINTS if is_dandelion else BEAUTY_HINTS
        elif simplified:
            item = QListWidgetItem("Gesture navigation active")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.effects_list.addItem(item)
            hints = DANDELION_LIVE_HINTS if is_dandelion else BEAUTY_HINTS
        else:
            for display, internal in EFFECT_ITEMS:
                if display is None:
                    separator = QListWidgetItem("— Interactive —")
                    separator.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.effects_list.addItem(separator)
                    continue
                QListWidgetItem(display, self.effects_list)
            self.effects_list.setCurrentRow(0)
            hints = GESTURE_HINTS

        for label, text in zip(self._gesture_labels, hints, strict=False):
            label.setText(text)
            label.setVisible(True)
        for label in self._gesture_labels[len(hints) :]:
            label.hide()

        self.brush_controls.setVisible(False)
        self.reveal_controls.setVisible(False)
        self._block_signals = False

    def show_dandelion_live_hints(self) -> None:
        self._apply_hint_list(DANDELION_LIVE_HINTS)

    def show_dandelion_paint_hints(self) -> None:
        self._apply_hint_list(DANDELION_PAINT_HINTS)

    def _apply_hint_list(self, hints: tuple[str, ...]) -> None:
        for label, text in zip(self._gesture_labels, hints, strict=False):
            label.setText(text)
            label.setVisible(True)
        for label in self._gesture_labels[len(hints) :]:
            label.hide()

    def select_effect(self, effect_name: str) -> None:
        """Programmatically select an effect without re-emitting the signal."""
        normalized = effect_name.strip().lower()
        display = self._effect_lookup.get(normalized, normalized.replace("_", " ").title())

        self._block_signals = True
        for row in range(self.effects_list.count()):
            item = self.effects_list.item(row)
            if item and item.text() == display:
                self.effects_list.setCurrentRow(row)
                break
        self._block_signals = False
        self._update_tool_panels(normalized)

    def _on_effect_changed(self, text: str) -> None:
        if not text or self._block_signals or text.startswith("—"):
            return
        for display, internal in EFFECT_ITEMS:
            if display == text and internal is not None:
                self._update_tool_panels(internal)
                self.effect_selected.emit(internal)
                return

    def _update_tool_panels(self, effect_name: str) -> None:
        self.brush_controls.setVisible(False)
        self.reveal_controls.setVisible(effect_name == "reveal")
