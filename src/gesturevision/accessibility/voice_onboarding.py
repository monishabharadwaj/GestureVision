from __future__ import annotations

"""Startup: blind enters by saying Beauty (voice only). Deaf enters via big button or auto countdown."""

import logging
import threading
import time
from typing import Any

from PyQt6.QtCore import QTimer, Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout

from gesturevision.accessibility.speech_utils import matches_beauty_trigger, transcribe_audio
from gesturevision.accessibility.tts_service import TextToSpeechService
from gesturevision.core.types import AccessibilityProfile

logger = logging.getLogger(__name__)


class AccessibilityOnboardingDialog(QDialog):
    """
    Deaf users: read the screen, click DANDELION or wait for countdown.
    Blind users: say "Beauty" anytime — voice listener runs in parallel from second zero.
    """

    beauty_detected = pyqtSignal()
    speech_heard = pyqtSignal(str)

    def __init__(
        self,
        onboarding_cfg: dict[str, Any],
        *,
        listen_seconds: int = 12,
        beauty_listen_seconds: int = 25,
        trigger_words: list[str] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("GestureVision")
        self.setModal(True)
        self.setMinimumWidth(620)
        self._selected = AccessibilityProfile.DANDELION
        self._resolved = False
        self._listen_seconds = listen_seconds
        self._beauty_listen_seconds = beauty_listen_seconds
        self._trigger_words = [word.lower() for word in (trigger_words or ["beauty"])]

        spoken = str(
            onboarding_cfg.get(
                "spoken_prompt",
                "Welcome. If you cannot see the screen, say Beauty now.",
            )
        ).strip()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        title = QLabel(str(onboarding_cfg.get("dandelion_title", "DANDELION — Visual Mode")))
        title.setObjectName("ProfileTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        visual_instructions = QLabel(
            str(
                onboarding_cfg.get(
                    "dandelion_instructions",
                    "You can SEE this screen.\n\n"
                    "Click the button below to enter Dandelion mode,\n"
                    "or wait for the countdown.\n\n"
                    "No sound needed. Everything will be shown as text.",
                )
            )
        )
        visual_instructions.setObjectName("CaptionBanner")
        visual_instructions.setWordWrap(True)
        visual_instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(visual_instructions)

        self._dandelion_button = QPushButton(
            str(onboarding_cfg.get("dandelion_button", "ENTER DANDELION MODE (I can see)"))
        )
        self._dandelion_button.setObjectName("ProfileButton")
        self._dandelion_button.setMinimumHeight(72)
        self._dandelion_button.clicked.connect(self._choose_dandelion)
        layout.addWidget(self._dandelion_button)

        self._countdown_label = QLabel("")
        self._countdown_label.setObjectName("StatusLabel")
        self._countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._countdown_label)

        self._progress = QProgressBar()
        self._progress.setRange(0, listen_seconds)
        self._progress.setValue(0)
        layout.addWidget(self._progress)

        beauty_hint = QLabel(
            str(
                onboarding_cfg.get(
                    "beauty_hint",
                    "Blind users (cannot see): say BEAUTY loudly anytime — camera starts automatically.",
                )
            )
        )
        beauty_hint.setObjectName("MutedLabel")
        beauty_hint.setWordWrap(True)
        beauty_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(beauty_hint)

        self._status_label = QLabel("Listening for BEAUTY right now…")
        self._status_label.setObjectName("CaptionBanner")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setWordWrap(True)
        layout.addWidget(self._status_label)

        self._tts = TextToSpeechService()
        self._tts.start()
        QTimer.singleShot(300, lambda: self._tts.speak(spoken))

        self.beauty_detected.connect(self._choose_beauty)
        self.speech_heard.connect(self._on_speech_heard)

        self._seconds_left = listen_seconds
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

        # Start beauty listener immediately — parallel to countdown and TTS.
        listener = threading.Thread(
            target=self._listen_for_beauty,
            name="VoiceOnboarding",
            daemon=True,
        )
        listener.start()

    @property
    def selected_profile(self) -> AccessibilityProfile:
        return self._selected

    def _on_speech_heard(self, text: str) -> None:
        self._status_label.setText(f'Heard: "{text}" — say BEAUTY for blind mode')

    def _tick(self) -> None:
        self._countdown_label.setText(
            f"Dandelion auto-starts in {self._seconds_left} second"
            f"{'' if self._seconds_left == 1 else 's'}…"
        )
        self._progress.setValue(self._listen_seconds - self._seconds_left)
        if self._seconds_left <= 0:
            self._finish(AccessibilityProfile.DANDELION)
            return
        self._seconds_left -= 1

    def _choose_dandelion(self) -> None:
        self._finish(AccessibilityProfile.DANDELION)

    def _choose_beauty(self) -> None:
        self._finish(AccessibilityProfile.BEAUTY)

    def _finish(self, profile: AccessibilityProfile) -> None:
        if self._resolved:
            return
        self._resolved = True
        self._selected = profile
        self._timer.stop()
        if profile == AccessibilityProfile.BEAUTY:
            self._status_label.setText("BEAUTY MODE — starting camera")
            self._tts.speak(
                "Beauty mode activated. Starting camera now. Show your hand when you hear camera started."
            )
        self.accept()

    def _listen_for_beauty(self) -> None:
        try:
            import speech_recognition as sr
        except ImportError:
            logger.warning("speech_recognition not installed — blind users need to say Beauty")
            return

        recognizer = sr.Recognizer()
        recognizer.energy_threshold = 300
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.6
        end_time = time.time() + self._beauty_listen_seconds

        while time.time() < end_time and not self._resolved:
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    remaining = max(1.0, end_time - time.time())
                    audio = recognizer.listen(
                        source,
                        timeout=min(4.0, remaining),
                        phrase_time_limit=5,
                    )
                text = transcribe_audio(recognizer, audio)
                if not text:
                    continue
                logger.info("Onboarding heard: %s", text)
                self.speech_heard.emit(text)
                if matches_beauty_trigger(text, self._trigger_words):
                    self.beauty_detected.emit()
                    return
            except Exception:
                continue

    def closeEvent(self, event) -> None:  # noqa: N802
        self._tts.shutdown()
        super().closeEvent(event)
