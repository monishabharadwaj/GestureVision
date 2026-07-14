from __future__ import annotations

"""Main application window with live camera pipeline controls."""

import logging
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction, QImage
from PyQt6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from gesturevision import __app_name__, __version__
from gesturevision.accessibility.feedback_manager import FeedbackManager
from gesturevision.accessibility.voice_commands import VoiceCommandService
from gesturevision.accessibility.profile_config import ProfileSettings
from gesturevision.app.controller import PipelineController
from gesturevision.app.state_machine import StateMachine
from gesturevision.core.events import DomainEvent, EventBus, EventType
from gesturevision.core.exceptions import GestureVisionError
from gesturevision.core.types import AccessibilityProfile, AppMode, PipelineMetrics
from gesturevision.ui.widgets.sidebar import Sidebar
from gesturevision.ui.widgets.status_bar import AppStatusBar
from gesturevision.ui.widgets.toolbar import Toolbar
from gesturevision.ui.widgets.video_widget import VideoWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Primary desktop window with sidebar, toolbar, video area, and status bar."""

    def __init__(
        self,
        configs: dict[str, dict[str, Any]],
        project_root: Path,
        event_bus: EventBus,
        state_machine: StateMachine,
        profile_settings: ProfileSettings | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._configs = configs
        self._app_config = configs["app"]
        self._project_root = project_root
        self._event_bus = event_bus
        self._state_machine = state_machine
        self._profile_settings = profile_settings or ProfileSettings(
            profile=AccessibilityProfile.STANDARD,
        )
        self._feedback_manager: FeedbackManager | None = None
        self._voice_commands: VoiceCommandService | None = None

        self._pipeline = PipelineController(
            configs,
            project_root,
            event_bus,
            profile_settings=self._profile_settings,
            parent=self,
        )

        self._apply_window_chrome()
        self._build_menu()
        self._build_layout()
        self._apply_profile_ui()
        self._load_theme()
        self._wire_events()

        logger.info("MainWindow ready (profile=%s)", self._profile_settings.profile.value)

    def begin_accessibility_session(self) -> None:
        """Auto-start camera and voice listening — no clicking for blind users."""
        if not self._profile_settings.is_accessibility_mode:
            return

        if self._profile_settings.audio_only:
            self.toolbar.hide()
            self.menuBar().hide()

        if self._profile_settings.auto_start_camera:
            # Brief delay so welcome TTS/caption can play first.
            delay = 1200 if self._profile_settings.audio_only else 800
            QTimer.singleShot(delay, self._auto_start_camera)

    def _auto_start_camera(self) -> None:
        if self._pipeline.is_running:
            return
        try:
            self._on_start_camera()
        except GestureVisionError as exc:
            self._on_pipeline_error(str(exc))

    def set_feedback_manager(self, manager: FeedbackManager) -> None:
        self._feedback_manager = manager

    def show_caption(self, text: str, duration_ms: int) -> None:
        self.video_widget.show_caption(text, duration_ms)

    def _apply_window_chrome(self) -> None:
        window_cfg = self._app_config.get("window", {})
        profile_tag = self._profile_settings.display_name or self._profile_settings.profile.value
        self.setWindowTitle(f"{__app_name__}  ·  {profile_tag}  ·  v{__version__}")
        self.resize(
            int(window_cfg.get("width", 1280)),
            int(window_cfg.get("height", 720)),
        )
        self.setMinimumSize(
            int(window_cfg.get("min_width", 960)),
            int(window_cfg.get("min_height", 540)),
        )

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        quit_action = QAction("E&xit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        help_menu = self.menuBar().addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _build_layout(self) -> None:
        central = QWidget(self)
        self.setCentralWidget(central)

        root_layout = QVBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.toolbar = Toolbar(self)
        root_layout.addWidget(self.toolbar)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(1)

        self.sidebar = Sidebar(self)
        self.video_widget = VideoWidget(self)

        splitter.addWidget(self.sidebar)
        splitter.addWidget(self.video_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 1000])

        root_layout.addWidget(splitter, stretch=1)

        self.status_bar = AppStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.set_status("Ready")
        self.status_bar.set_mode(self._state_machine.mode.value)
        self.status_bar.set_effect("original")
        self.status_bar.set_gesture("—")
        self.status_bar.set_fps(0.0)

    def _apply_profile_ui(self) -> None:
        if not self._profile_settings.is_accessibility_mode:
            return

        is_dandelion = self._profile_settings.profile == AccessibilityProfile.DANDELION
        self.sidebar.apply_accessibility_mode(
            profile_name=self._profile_settings.display_name,
            simplified=self._profile_settings.simplified_ui,
            reduced_effects=self._profile_settings.reduced_effects,
            audio_only=self._profile_settings.audio_only,
            is_dandelion=is_dandelion,
        )
        self.video_widget.set_audio_only(self._profile_settings.hide_video)
        self.toolbar.start_button.setText("START CAMERA")
        self.toolbar.stop_button.setText("STOP")

        if self._profile_settings.audio_only:
            self.video_widget.show_placeholder("Audio mode — camera starting automatically…")
        elif self._profile_settings.profile == AccessibilityProfile.DANDELION:
            a11y_cfg = self._configs.get("accessibility", {}).get("accessibility", {})
            apps = a11y_cfg.get("apps", {})
            touch_ids = self._profile_settings.touch_bar
            targets = [
                (app_id, str(apps.get(app_id, {}).get("label", app_id.title())))
                for app_id in touch_ids
            ]
            self.video_widget.set_touch_targets(targets)
            self.video_widget.set_next_step(
                "NEXT → Point at TOUCH BAR below and hold  |  SAY: play music, open youtube, open chrome"
            )

        if self._profile_settings.profile in {
            AccessibilityProfile.BEAUTY,
            AccessibilityProfile.DANDELION,
        }:
            a11y_cfg = self._configs.get("accessibility", {}).get("accessibility", {})
            phrases = a11y_cfg.get("voice_commands", {})
            apps = a11y_cfg.get("apps", {})
            self._voice_commands = VoiceCommandService(phrases, apps, parent=self)

    def _load_theme(self) -> None:
        if self._profile_settings.is_accessibility_mode:
            theme_name = self._profile_settings.theme
        else:
            theme_name = self._app_config.get("theme", "dark")
        theme_path = self._project_root / "assets" / "themes" / f"{theme_name}.qss"
        if not theme_path.is_file():
            logger.warning("Theme not found: %s", theme_path)
            return
        stylesheet = theme_path.read_text(encoding="utf-8")
        self.setStyleSheet(stylesheet)
        logger.debug("Applied theme: %s", theme_path)

    def _wire_events(self) -> None:
        self._event_bus.subscribe(EventType.MODE_CHANGED, self._on_mode_changed)

        self.toolbar.start_clicked.connect(self._on_start_camera)
        self.toolbar.stop_clicked.connect(self._on_stop_camera)
        self.sidebar.effect_selected.connect(self._on_effect_selected)
        self.sidebar.brush_type_changed.connect(self._pipeline.set_brush_type)
        self.sidebar.brush_color_changed.connect(self._pipeline.set_brush_color)
        self.sidebar.reveal_filter_changed.connect(self._pipeline.set_reveal_overlay)

        self._pipeline.frame_ready.connect(self._on_frame_ready)
        self._pipeline.status_changed.connect(self._on_status_changed)
        self._pipeline.gesture_changed.connect(self.status_bar.set_gesture)
        self._pipeline.effect_switch_requested.connect(self._on_gesture_effect_switch)
        self._pipeline.parameter_changed.connect(self._on_parameter_changed)
        self._pipeline.screenshot_captured.connect(self._on_screenshot_captured)
        self._pipeline.pause_toggle_requested.connect(self._on_pause_toggle)
        self._pipeline.error_occurred.connect(self._on_pipeline_error)
        self._pipeline.menu_changed.connect(self._on_menu_changed)
        self._pipeline.menu_closed.connect(self.video_widget.hide_menu)
        self._pipeline.next_step_changed.connect(self.video_widget.set_next_step)
        self._pipeline.touch_hover.connect(self.video_widget.set_touch_hover)
        self._pipeline.dialogue_updated.connect(self._on_dialogue_updated)
        self._pipeline.paint_mode_changed.connect(self._on_paint_mode_changed)
        self._pipeline.paint_feedback_changed.connect(self._on_paint_feedback)

        if self._voice_commands is not None:
            self._voice_commands.command_recognized.connect(self._on_voice_command)
            self._voice_commands.heard_text.connect(self._on_voice_heard)

    def _on_voice_command(self, command_id: str, spoken_text: str) -> None:
        if self._pipeline.conversation_active():
            return
        if self._profile_settings.audio_only and self._feedback_manager is not None:
            self._feedback_manager.announce(f'You said: {spoken_text}')
        elif self._profile_settings.visual_captions:
            self.video_widget.show_caption(f'YOU SAID: "{spoken_text.upper()}"', 3000)
        self._pipeline.handle_voice_command(command_id, spoken_text)

    def _on_voice_heard(self, text: str) -> None:
        if not text:
            return
        if self._pipeline.conversation_active():
            self._pipeline.handle_conversation_utterance(text)
            return
        if self._profile_settings.audio_only:
            return
        self.video_widget.set_next_step(f'HEARING… "{text}"')

    def _on_dialogue_updated(self, agent_text: str, user_text: str, detail_text: str = "") -> None:
        if not agent_text and not detail_text:
            return
        if self._pipeline.active_effect == "brush":
            return
        if self._profile_settings.visual_captions:
            self.video_widget.show_dialogue(agent_text, user_text, detail_text)
        elif self._profile_settings.audio_only and detail_text.strip() and self._feedback_manager:
            self._feedback_manager.announce(detail_text)

    def _on_paint_mode_changed(self, active: bool) -> None:
        self.video_widget.set_paint_mode(active)
        if active and self._profile_settings.profile == AccessibilityProfile.DANDELION:
            self.sidebar.select_effect("brush")
            self.sidebar.brush_controls.setVisible(True)
        elif self._profile_settings.profile == AccessibilityProfile.DANDELION:
            self.sidebar.brush_controls.setVisible(False)

    def _on_menu_changed(self, labels: list, active_index: int) -> None:
        self.video_widget.show_menu(labels, active_index)

    def _on_mode_changed(self, event: DomainEvent) -> None:
        mode = str(event.payload.get("to", self._state_machine.mode.value))
        self.status_bar.set_mode(mode)

    def _on_status_changed(self, message: str) -> None:
        self.status_bar.set_status(message)
        if self._pipeline.active_effect == "brush":
            return
        if self._profile_settings.visual_captions and self._profile_settings.is_accessibility_mode:
            self.video_widget.show_caption(message, self._profile_settings.caption_duration_ms)
        if self._profile_settings.audio_only and self._feedback_manager is not None:
            self._feedback_manager.announce(message)

    def _on_paint_feedback(self, message: str, brush: str, background: str) -> None:
        if self._profile_settings.profile == AccessibilityProfile.DANDELION:
            self.video_widget.show_paint_feedback(message, brush=brush, background=background)

    def _on_start_camera(self) -> None:
        try:
            self._pipeline.start()
            self.toolbar.start_button.setEnabled(False)
            self.toolbar.stop_button.setEnabled(True)
            if self._voice_commands is not None:
                self._voice_commands.start()
            self._on_status_changed("Camera live — show your hand to the webcam")
        except GestureVisionError as exc:
            self._on_pipeline_error(str(exc))

    def _on_stop_camera(self) -> None:
        if self._voice_commands is not None:
            self._voice_commands.stop()
        self._pipeline.stop()
        self.toolbar.start_button.setEnabled(True)
        self.toolbar.stop_button.setEnabled(False)
        self.video_widget.show_placeholder("Camera stopped")
        self.status_bar.set_fps(0.0)
        self.status_bar.set_gesture("—")

    def _on_frame_ready(self, image: QImage, metrics: PipelineMetrics) -> None:
        self.video_widget.update_frame(image)
        self.status_bar.set_fps(metrics.fps)

    def _on_pipeline_error(self, message: str) -> None:
        logger.error("Pipeline error: %s", message)
        self.toolbar.start_button.setEnabled(True)
        self.toolbar.stop_button.setEnabled(False)
        self.status_bar.set_status(f"Error: {message}")
        QMessageBox.critical(self, "Camera Error", message)

    def _on_gesture_effect_switch(self, effect_name: str) -> None:
        self._pipeline.set_active_effect(effect_name)
        self.sidebar.select_effect(effect_name)
        self.status_bar.set_effect(effect_name)
        self._event_bus.publish(
            DomainEvent(
                type=EventType.EFFECT_CHANGED,
                payload={"effect": effect_name, "source": "gesture"},
            )
        )

    def _on_parameter_changed(self, target: str, value: float) -> None:
        effect = self._pipeline.active_effect
        if effect == "brush":
            self._on_status_changed(f"Brush size: {value:.0%}")
        else:
            self._on_status_changed(f"Adjustment: {value:.0%}")

    def _on_screenshot_captured(self, path: str) -> None:
        self._on_status_changed(f"Screenshot saved: {Path(path).name}")

    def _on_pause_toggle(self) -> None:
        if self._state_machine.mode == AppMode.PAUSED:
            self._state_machine.transition(AppMode.LIVE)
            self._on_status_changed("Resumed")
        else:
            self._state_machine.transition(AppMode.PAUSED)
            self._on_status_changed("Paused — show fist again to resume")

    def _on_effect_selected(self, effect_name: str) -> None:
        self._pipeline.set_active_effect(effect_name)
        self.sidebar._update_tool_panels(effect_name)
        self.status_bar.set_effect(effect_name)
        self._event_bus.publish(
            DomainEvent(
                type=EventType.EFFECT_CHANGED,
                payload={"effect": effect_name},
            )
        )

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {__app_name__}",
            f"<b>{__app_name__}</b><br>"
            f"Version {__version__}<br><br>"
            "Real-time finger-controlled computer vision system.<br>"
            "Phase 5 — Beauty hears everything. Dandelion sees and navigates with hands.",
        )

    def shutdown(self) -> None:
        """Release pipeline resources."""
        if self._voice_commands is not None:
            self._voice_commands.stop()
        self._pipeline.shutdown()

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt naming
        logger.info("MainWindow closing")
        self.shutdown()
        super().closeEvent(event)
