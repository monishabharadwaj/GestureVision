from __future__ import annotations

"""Live video display widget."""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import QLabel, QStackedLayout, QWidget

from gesturevision.accessibility.picture_cards import (
    LIVE_ACTION_BOARD,
    LIVE_POSE_STRIP,
    PAINT_POSE_STRIP,
    PictureCard,
    card_for_gesture,
    card_for_text,
)
from gesturevision.ui.widgets.caption_overlay import CaptionOverlay
from gesturevision.ui.widgets.gesture_flash_overlay import GestureFlashOverlay
from gesturevision.ui.widgets.gesture_menu_overlay import GestureMenuOverlay
from gesturevision.ui.widgets.learning_panel_overlay import LearningPanelOverlay
from gesturevision.ui.widgets.next_step_overlay import NextStepOverlay
from gesturevision.ui.widgets.gesture_pose_overlay import GesturePoseOverlay
from gesturevision.ui.widgets.paint_hud_overlay import PaintHudOverlay
from gesturevision.ui.widgets.picture_board_overlay import PictureBoardOverlay
from gesturevision.ui.widgets.pictograph_caption_overlay import (
    SILENT_GESTURES,
    PictographCaptionOverlay,
)
from gesturevision.ui.widgets.touch_pad_overlay import TouchPadOverlay
from gesturevision.ui.widgets.toast_overlay import ToastOverlay
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
        self.toast_overlay = ToastOverlay(self._video_container)
        self.gesture_flash = GestureFlashOverlay(self._video_container)
        self.gesture_pose = GesturePoseOverlay(self._video_container)
        self.picture_board = PictureBoardOverlay(self._video_container)
        self.pictograph_caption = PictographCaptionOverlay(self._video_container)
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
        self._picture_mode = False

        for overlay in (
            self.caption_overlay,
            self.menu_overlay,
            self.next_step_overlay,
            self.touch_pad,
            self.toast_overlay,
            self.gesture_flash,
            self.gesture_pose,
            self.picture_board,
            self.pictograph_caption,
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

    def set_touch_hover(self, app_id: str, progress: float = 0.0) -> None:
        self.touch_pad.set_hover(app_id or None, progress)

    def show_toast(self, message: str, kind: str = "info") -> None:
        self.toast_overlay.show_toast(message, kind)
        self._layout_layers()

    def set_picture_mode(self, enabled: bool) -> None:
        """Picture/ASL mode — emoji pictographs instead of reading text."""
        self._picture_mode = enabled
        if enabled and not self._audio_only:
            self.gesture_pose.set_poses(LIVE_POSE_STRIP)
            self.picture_board.set_cards(list(LIVE_ACTION_BOARD))
            self.next_step_overlay.hide()
        else:
            self.gesture_pose.hide_panel()
            self.picture_board.hide_board()
            if not self._paint_mode:
                self.next_step_overlay.show()
        self._layout_layers()

    def show_pictograph(self, card: PictureCard, duration_ms: int = 1200) -> None:
        if self._audio_only or self._paint_mode:
            return
        if card.card_id in {"touch", "size"}:
            # Highlight only — never cover camera while pointing/pinching.
            self.picture_board.highlight(card.card_id)
            return
        self.pictograph_caption.show_card(card, duration_ms)
        self.picture_board.highlight(card.card_id)
        self._layout_layers()

    def highlight_picture(self, card_id: str | None) -> None:
        if self._picture_mode:
            self.picture_board.highlight(card_id or "")

    def highlight_pose(self, gesture: str) -> None:
        if self._picture_mode:
            normalized = gesture.replace(" ", "_").lower()
            self.gesture_pose.highlight_gesture(normalized if normalized != "—" else "")

    def flash_gesture(self, gesture_name: str, action_label: str = "") -> None:
        if self._audio_only:
            return
        key = gesture_name.replace(" ", "_").lower()
        if key in SILENT_GESTURES:
            self.highlight_pose(key)
            return
        # Paint mode: keep HUD clear — no fullscreen flash covering ❌ EXIT.
        if self._paint_mode:
            return
        if self._picture_mode:
            card = card_for_gesture(key)
            if card is None and action_label:
                card = card_for_text(action_label)
            if card is not None:
                self.show_pictograph(card, 1000)
                return
        self.gesture_flash.flash(gesture_name, action_label)
        self._layout_layers()

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
        if self._picture_mode:
            card = card_for_text(text)
            # Skip continuous / noisy captions that would spam chips.
            lowered = text.lower()
            if any(token in lowered for token in ("index", "touch bar", "brush size", "hearing")):
                return
            if card is not None:
                self.show_pictograph(card, min(duration_ms, 1200))
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
            self.pictograph_caption.hide()
            self.gesture_flash.hide()
            self.menu_overlay.hide_menu()
            self.touch_pad.hide_bar()
            self.picture_board.hide_board()
            self.next_step_overlay.hide()
            if self._picture_mode:
                self.gesture_pose.set_poses(PAINT_POSE_STRIP)
            self.paint_hud.show_status(
                "☝ draw  ·  👌 brush  ·  🤘 ink  ·  ✌ look  ·  👍 3D",
                brush="Neon",
                background="Live camera",
            )
        else:
            self.paint_hud.hide()
            if self._picture_mode:
                self.gesture_pose.set_poses(LIVE_POSE_STRIP)
                self.picture_board.set_cards(list(LIVE_ACTION_BOARD))
                self.picture_board.show()
            elif not self._audio_only and self._touch_bar_active:
                self.touch_pad.show()
            if not self._picture_mode:
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

        pose_h = 0
        picture_board_h = 0
        if self._picture_mode and self.gesture_pose.isVisible():
            pose_h = min(72, max(56, h // 9))
        if self._picture_mode and not self._paint_mode and self.picture_board.isVisible():
            picture_board_h = min(110, max(80, h // 6))

        top_h = 0 if self._picture_mode else min(88, max(56, h // 7))
        bottom_touch_h = 0 if self._paint_mode else min(130, max(90, h // 5))
        lesson_h = 0 if self._paint_mode or not self.learning_panel.isVisible() else int(h * 0.38)
        paint_hud_h = min(150, max(110, h // 5)) if self._paint_mode else 0
        dialogue_h = min(int(h * 0.28), 220) if self.dialogue_overlay.isVisible() else 0

        y_cursor = 0
        if pose_h and self.gesture_pose.isVisible():
            self.gesture_pose.setGeometry(0, y_cursor, w, pose_h)
            self.gesture_pose.raise_()
            y_cursor += pose_h

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
            # Thin middle band — never cover pose strip or picture board.
            band_top = pose_h + 8
            band_h = max(80, h - band_top - picture_board_h - bottom_touch_h - 20)
            self.caption_overlay.setGeometry(0, band_top, w, min(band_h, 160))

        if self.learning_panel.isVisible():
            self.learning_panel.setGeometry(
                0,
                h - lesson_h - bottom_touch_h - picture_board_h - paint_hud_h,
                w,
                lesson_h,
            )
            self.learning_panel.raise_()

        if self._paint_mode and self.paint_hud.isVisible():
            self.paint_hud.setGeometry(0, h - paint_hud_h, w, paint_hud_h)
            self.paint_hud.raise_()

        if bottom_touch_h and self.touch_pad.isVisible():
            y_touch = h - bottom_touch_h - picture_board_h
            self.touch_pad.setGeometry(0, y_touch, w, bottom_touch_h)
            self.touch_pad.raise_()

        if picture_board_h and self.picture_board.isVisible():
            y_board = h - picture_board_h - (bottom_touch_h if self.touch_pad.isVisible() else 0)
            self.picture_board.setGeometry(0, y_board, w, picture_board_h)
            self.picture_board.raise_()

        if self.toast_overlay.isVisible():
            self.toast_overlay.setGeometry(w - min(360, w // 2), pose_h + 8, min(360, w // 2), 90)
            self.toast_overlay.raise_()

        if self.gesture_flash.isVisible() and not self._paint_mode:
            # Compact center strip — keep bottom UI readable.
            flash_h = min(160, h // 4)
            self.gesture_flash.setGeometry(0, (h - flash_h) // 2, w, flash_h)

        if self.pictograph_caption.isVisible() and not self._paint_mode:
            chip_w = min(200, w // 3)
            chip_h = 64
            self.pictograph_caption.setGeometry(w - chip_w - 8, pose_h + 8, chip_w, chip_h)
            self.pictograph_caption.raise_()

    def resizeEvent(self, event) -> None:  # noqa: N802 — Qt naming
        super().resizeEvent(event)
        self._layout_layers()
