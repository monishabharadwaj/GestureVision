from __future__ import annotations

"""Live video display widget."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QStackedLayout, QWidget

from gesturevision.ui.widgets.caption_overlay import CaptionOverlay
from gesturevision.ui.widgets.gesture_menu_overlay import GestureMenuOverlay
from gesturevision.ui.widgets.learning_panel_overlay import LearningPanelOverlay
from gesturevision.ui.widgets.next_step_overlay import NextStepOverlay
from gesturevision.ui.widgets.paint_hud_overlay import PaintHudOverlay
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
        self._video_container.setStyleSheet("background-color: #000000;")

        self._video_label = QLabel(self._video_container)
        self._video_label.setObjectName("VideoFeed")
        self._video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._video_label.setScaledContents(True)

        self.caption_overlay = CaptionOverlay(self._video_container)
        self.menu_overlay = GestureMenuOverlay(self._video_container)
        self.next_step_overlay = NextStepOverlay(self._video_container)
        self.touch_pad = TouchPadOverlay(self._video_container)
        self.dialogue_overlay = VisualDialogueOverlay(self._video_container)
        self.learning_panel = LearningPanelOverlay(self._video_container)
        self.paint_hud = PaintHudOverlay(self._video_container)

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
        self._touch_bar_active = False
        self._paint_mode = False

        for overlay in (
            self.caption_overlay,
            self.menu_overlay,
            self.next_step_overlay,
            self.touch_pad,
            self.dialogue_overlay,
            self.learning_panel,
            self.paint_hud,
        ):
            overlay.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def set_audio_only(self, enabled: bool) -> None:
        self._audio_only = enabled

    def show_placeholder(self, message: str) -> None:
        """Return to the idle placeholder state."""
        self.placeholder.setText(message)
        self._stack.setCurrentWidget(self.placeholder)
        self._video_label.clear()
        self.caption_overlay.hide()
        self.menu_overlay.hide_menu()
        self.paint_hud.hide()

    def set_touch_targets(self, targets: list[tuple[str, str]]) -> None:
        self._touch_bar_active = bool(targets)
        self.touch_pad.set_targets(targets)
        self._layout_layers()

    def set_touch_hover(self, app_id: str) -> None:
        self.touch_pad.set_hover(app_id or None)

    def set_next_step(self, text: str) -> None:
        if self._paint_mode:
            return
        self.next_step_overlay.set_message(text)
        self._layout_layers()

    def show_caption(self, text: str, duration_ms: int = 4000) -> None:
        """Display a large timed caption over the video area."""
        if self._paint_mode:
            self.show_paint_feedback(text)
            return
        self.caption_overlay.show_caption(text, duration_ms)
        self._layout_layers()

    def set_paint_mode(self, active: bool) -> None:
        """Maximize visible camera for painting — hide blocking overlays."""
        self._paint_mode = active
        if active:
            self.learning_panel.hide_lesson()
            self.dialogue_overlay.hide()
            self.caption_overlay.hide()
            self.menu_overlay.hide_menu()
            self.touch_pad.hide_bar()
            self.next_step_overlay.hide()
            self.paint_hud.show_status(
                "PAINT STUDIO — point ☝ index finger at your face to draw",
                brush="Neon",
                background="Live camera",
            )
        else:
            self.paint_hud.hide()
            if not self._audio_only and self._touch_bar_active:
                self.touch_pad.show()
            self.next_step_overlay.show()
        self._layout_layers()

    def show_paint_feedback(self, message: str, *, brush: str = "", background: str = "") -> None:
        self.paint_hud.show_status(message, brush=brush, background=background)
        self._layout_layers()

    def update_paint_detail(self, brush: str, background: str) -> None:
        self.paint_hud.set_detail(brush, background)
        self.paint_hud.show()
        self._layout_layers()

    def show_dialogue(self, agent: str, user: str = "", detail: str = "") -> None:
        """Show a persistent agent/user exchange for deaf users."""
        if self._paint_mode:
            return
        if agent:
            self.dialogue_overlay.show_exchange(agent, user)
            self.caption_overlay.show_caption(agent, 8000)
        if detail.strip():
            topic = user.strip() or "your topic"
            self.learning_panel.show_lesson(topic, detail)
        else:
            self.learning_panel.hide_lesson()
        self._layout_layers()

    def show_menu(self, labels: list[str], active_index: int) -> None:
        self.menu_overlay.show_menu(labels, active_index)
        self._layout_layers()

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
        self._video_label.setPixmap(pixmap)
        if self._stack.currentWidget() is not self._video_container:
            self._stack.setCurrentWidget(self._video_container)
        self._layout_layers()

    def _layout_layers(self) -> None:
        """Keep the camera full-screen; overlays only use thin edge bands."""
        w = max(self._video_container.width(), 1)
        h = max(self._video_container.height(), 1)

        self._video_label.setGeometry(0, 0, w, h)
        self._video_label.lower()

        top_h = min(88, max(56, h // 7))
        bottom_touch_h = 0 if self._paint_mode else min(130, max(90, h // 5))
        lesson_h = 0 if self._paint_mode or not self.learning_panel.isVisible() else int(h * 0.38)
        paint_hud_h = min(110, max(80, h // 6)) if self._paint_mode else 0
        dialogue_h = min(int(h * 0.28), 220) if self.dialogue_overlay.isVisible() else 0

        y_cursor = 0
        if self.next_step_overlay.isVisible() and not self._paint_mode:
            self.next_step_overlay.setGeometry(0, y_cursor, w, top_h)
            self.next_step_overlay.raise_()
            y_cursor += top_h

        if self.dialogue_overlay.isVisible():
            self.dialogue_overlay.setGeometry(0, y_cursor, w, dialogue_h)
            self.dialogue_overlay.raise_()
            y_cursor += dialogue_h

        if self.menu_overlay.isVisible():
            self.menu_overlay.setGeometry(0, y_cursor, w, h - y_cursor - bottom_touch_h - lesson_h - paint_hud_h)
            self.menu_overlay.raise_()

        if self.caption_overlay.isVisible():
            self.caption_overlay.setGeometry(0, 0, w, h)

        if self.learning_panel.isVisible():
            self.learning_panel.setGeometry(0, h - lesson_h - bottom_touch_h - paint_hud_h, w, lesson_h)
            self.learning_panel.raise_()

        if self._paint_mode and self.paint_hud.isVisible():
            self.paint_hud.setGeometry(0, h - paint_hud_h, w, paint_hud_h)
            self.paint_hud.raise_()

        if bottom_touch_h and self.touch_pad.isVisible():
            self.touch_pad.setGeometry(0, h - bottom_touch_h, w, bottom_touch_h)
            self.touch_pad.raise_()

    def resizeEvent(self, event) -> None:  # noqa: N802 — Qt naming
        super().resizeEvent(event)
        self._layout_layers()
