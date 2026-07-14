from __future__ import annotations

"""Live video display widget."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QStackedLayout, QVBoxLayout, QWidget

from gesturevision.ui.widgets.caption_overlay import CaptionOverlay
from gesturevision.ui.widgets.gesture_menu_overlay import GestureMenuOverlay
from gesturevision.ui.widgets.next_step_overlay import NextStepOverlay
from gesturevision.ui.widgets.learning_panel_overlay import LearningPanelOverlay
from gesturevision.ui.widgets.touch_pad_overlay import TouchPadOverlay
from gesturevision.ui.widgets.visual_dialogue_overlay import VisualDialogueOverlay


class VideoWidget(QWidget):
    """Renders processed camera frames from the perception pipeline."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._stack = QStackedLayout(self)
        self._stack.setContentsMargins(0, 0, 0, 0)

        self.placeholder = QLabel("Press Start Camera to begin hand tracking")
        self.placeholder.setObjectName("VideoPlaceholder")
        self.placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._video_container = QWidget()
        video_layout = QVBoxLayout(self._video_container)
        video_layout.setContentsMargins(0, 0, 0, 0)

        self._video_label = QLabel()
        self._video_label.setObjectName("VideoPlaceholder")
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setScaledContents(True)
        video_layout.addWidget(self._video_label)

        self.caption_overlay = CaptionOverlay(self._video_container)
        self.menu_overlay = GestureMenuOverlay(self._video_container)
        self.next_step_overlay = NextStepOverlay(self._video_container)
        self.touch_pad = TouchPadOverlay(self._video_container)
        self.dialogue_overlay = VisualDialogueOverlay(self._video_container)
        self.learning_panel = LearningPanelOverlay(self._video_container)

        self._audio_panel = QLabel(
            "AUDIO MODE\n\n"
            "You do not need to see the screen.\n"
            "Show your hand — the app will speak every action."
        )
        self._audio_panel.setObjectName("VideoPlaceholder")
        self._audio_panel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._audio_panel.setWordWrap(True)

        self._stack.addWidget(self.placeholder)
        self._stack.addWidget(self._video_container)
        self._stack.addWidget(self._audio_panel)
        self._stack.setCurrentWidget(self.placeholder)
        self._audio_only = False

    def set_audio_only(self, enabled: bool) -> None:
        self._audio_only = enabled

    def show_placeholder(self, message: str) -> None:
        """Return to the idle placeholder state."""
        self.placeholder.setText(message)
        self._stack.setCurrentWidget(self.placeholder)
        self._video_label.clear()
        self.caption_overlay.hide()
        self.menu_overlay.hide_menu()

    def set_touch_targets(self, targets: list[tuple[str, str]]) -> None:
        self.touch_pad.set_targets(targets)

    def set_touch_hover(self, app_id: str) -> None:
        self.touch_pad.set_hover(app_id or None)

    def set_next_step(self, text: str) -> None:
        self.next_step_overlay.set_message(text)

    def show_caption(self, text: str, duration_ms: int = 4000) -> None:
        """Display a large timed caption over the video area."""
        self.caption_overlay.show_caption(text, duration_ms)

    def show_dialogue(self, agent: str, user: str = "", detail: str = "") -> None:
        """Show a persistent agent/user exchange for deaf users."""
        if agent:
            self.dialogue_overlay.show_exchange(agent, user)
            self.caption_overlay.show_caption(agent, 8000)
        if detail.strip():
            topic = user.strip() or "your topic"
            self.learning_panel.show_lesson(topic, detail)
        else:
            self.learning_panel.hide_lesson()

    def show_menu(self, labels: list[str], active_index: int) -> None:
        self.menu_overlay.show_menu(labels, active_index)

    def update_menu_selection(self, active_index: int) -> None:
        self.menu_overlay.update_selection(active_index)

    def hide_menu(self) -> None:
        self.menu_overlay.hide_menu()

    def update_frame(self, image: QImage) -> None:
        """Display a new frame scaled to the widget size."""
        if image.isNull():
            return

        if self._audio_only:
            if self._stack.currentWidget() is not self._audio_panel:
                self._stack.setCurrentWidget(self._audio_panel)
            return

        pixmap = QPixmap.fromImage(image)
        if not self._video_label.hasScaledContents():
            self._video_label.setScaledContents(True)
        self._video_label.setPixmap(pixmap)
        if self._stack.currentWidget() is not self._video_container:
            self._stack.setCurrentWidget(self._video_container)
        self.caption_overlay.resize(self._video_container.size())
        self.menu_overlay.resize(self._video_container.size())
        self.next_step_overlay.resize(self._video_container.size())
        self.touch_pad.resize(self._video_container.size())
        self.dialogue_overlay.resize(self._video_container.size())
        self.learning_panel.resize(self._video_container.size())

    def resizeEvent(self, event) -> None:  # noqa: N802 — Qt naming
        super().resizeEvent(event)
        if hasattr(self, "caption_overlay"):
            self.caption_overlay.resize(self._video_container.size())
            self.menu_overlay.resize(self._video_container.size())
            self.next_step_overlay.resize(self._video_container.size())
            self.dialogue_overlay.resize(self._video_container.size())
        self.learning_panel.resize(self._video_container.size())
        self.touch_pad.resize(self._video_container.size())
