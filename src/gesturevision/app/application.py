from __future__ import annotations

"""Top-level application orchestration."""

import logging
import sys
from typing import Any

from PyQt6.QtWidgets import QApplication

from gesturevision import __app_name__, __version__
from gesturevision.accessibility.feedback_manager import FeedbackManager
from gesturevision.accessibility.profile_config import load_profile_settings
from gesturevision.accessibility.voice_onboarding import AccessibilityOnboardingDialog
from gesturevision.app.state_machine import StateMachine
from gesturevision.core.events import DomainEvent, EventBus, EventType
from gesturevision.core.types import AccessibilityProfile
from gesturevision.ui.main_window import MainWindow
from gesturevision.utils.config_loader import ConfigLoader
from gesturevision.utils.logger import setup_logging

logger = logging.getLogger(__name__)


class Application:
    """Boots configuration, logging, the event bus, and the main window."""

    def __init__(self) -> None:
        self.config_loader = ConfigLoader()
        self.project_root = self.config_loader.project_root
        self.configs: dict[str, dict[str, Any]] = {}
        self.event_bus = EventBus()
        self.state_machine = StateMachine(self.event_bus)
        self.qt_app: QApplication | None = None
        self.main_window: MainWindow | None = None
        self.feedback_manager: FeedbackManager | None = None
        self.profile = AccessibilityProfile.DANDELION

    def initialize(self) -> None:
        """Load config, set up logging, and prepare runtime directories."""
        self.configs = self.config_loader.load_all()
        setup_logging(self.project_root, self.configs.get("logging"))

        app_cfg = self.configs["app"]
        for key in ("logs", "recordings", "screenshots", "models"):
            relative = app_cfg.get("paths", {}).get(key, key)
            self.config_loader.resolve_path(relative).mkdir(parents=True, exist_ok=True)

        logger.info("%s v%s initializing (Phase 5)", __app_name__, __version__)
        logger.info("Project root: %s", self.project_root)

    def _resolve_startup_profile(self) -> AccessibilityProfile:
        a11y_cfg = self.configs.get("accessibility", {}).get("accessibility", {})
        if not a11y_cfg.get("startup_prompt", True):
            default = str(a11y_cfg.get("default_profile", "dandelion"))
            try:
                return AccessibilityProfile(default)
            except ValueError:
                return AccessibilityProfile.DANDELION

        onboarding = a11y_cfg.get("onboarding", {})
        dialog = AccessibilityOnboardingDialog(
            onboarding,
            listen_seconds=int(a11y_cfg.get("voice_listen_seconds", 15)),
            beauty_listen_seconds=int(a11y_cfg.get("beauty_listen_seconds", 30)),
            trigger_words=list(a11y_cfg.get("voice_trigger_words", ["beauty"])),
        )
        dialog.setStyleSheet(self._load_theme_text("accessibility_high_contrast"))
        if dialog.exec():
            return dialog.selected_profile
        return AccessibilityProfile.DANDELION

    def _load_theme_text(self, theme_name: str) -> str:
        theme_path = self.project_root / "assets" / "themes" / f"{theme_name}.qss"
        if theme_path.is_file():
            return theme_path.read_text(encoding="utf-8")
        return ""

    def run(self) -> int:
        """Create the Qt application, show the main window, and enter the event loop."""
        self.initialize()

        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName(__app_name__)
        self.qt_app.setApplicationVersion(__version__)
        self.qt_app.setOrganizationName(
            self.configs["app"].get("organization", "GestureVision")
        )

        self.profile = self._resolve_startup_profile()
        profile_settings = load_profile_settings(self.configs["accessibility"], self.profile)

        self.main_window = MainWindow(
            configs=self.configs,
            project_root=self.project_root,
            event_bus=self.event_bus,
            state_machine=self.state_machine,
            profile_settings=profile_settings,
        )

        self.feedback_manager = FeedbackManager(
            self.event_bus,
            profile_settings,
            parent=self.main_window,
        )
        self.feedback_manager.caption_requested.connect(self.main_window.show_caption)
        self.main_window.set_feedback_manager(self.feedback_manager)

        self.main_window.show()
        self.feedback_manager.announce_welcome()
        self.main_window.begin_accessibility_session()

        self.event_bus.publish(
            DomainEvent(
                type=EventType.APP_STARTED,
                payload={
                    "version": __version__,
                    "phase": 5,
                    "profile": self.profile.value,
                },
            )
        )
        self.event_bus.publish(
            DomainEvent(
                type=EventType.PROFILE_CHANGED,
                payload={"profile": self.profile.value},
            )
        )
        logger.info(
            "Application started — Phase 5 accessibility (%s mode)",
            self.profile.value,
        )

        exit_code = self.qt_app.exec()
        self.shutdown()
        return exit_code

    def shutdown(self) -> None:
        """Publish shutdown and clear the event bus."""
        if self.feedback_manager is not None:
            self.feedback_manager.shutdown()
            self.feedback_manager = None
        if self.main_window is not None:
            self.main_window.shutdown()
        logger.info("Shutting down")
        self.event_bus.publish(DomainEvent(type=EventType.APP_STOPPING, payload={}))
        self.event_bus.clear()
