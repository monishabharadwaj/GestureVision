from __future__ import annotations

"""Voice commands — deaf and blind users can speak; matching is flexible."""

import logging
import threading
from typing import Any

from PyQt6.QtCore import QObject, pyqtSignal

from gesturevision.accessibility.voice_parser import build_phrase_map, match_spoken_command

logger = logging.getLogger(__name__)


class VoiceCommandService(QObject):
    """Background microphone listener with natural-language command matching."""

    command_recognized = pyqtSignal(str, str)  # command_id, spoken_text
    listening_changed = pyqtSignal(bool)
    heard_text = pyqtSignal(str)

    def __init__(
        self,
        phrases: dict[str, list[str]] | None = None,
        apps: dict[str, Any] | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._phrase_map = build_phrase_map(phrases or {}, apps or {})
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._running = False

    def start(self) -> None:
        if self._running:
            return
        self._stop.clear()
        self._running = True
        self._thread = threading.Thread(target=self._loop, name="VoiceCommands", daemon=True)
        self._thread.start()
        self.listening_changed.emit(True)
        logger.info("Voice commands started")

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._running = False
        self.listening_changed.emit(False)

    def _loop(self) -> None:
        try:
            import speech_recognition as sr
        except ImportError:
            logger.warning("speech_recognition not installed — voice commands disabled")
            return

        from gesturevision.accessibility.speech_utils import transcribe_audio

        recognizer = sr.Recognizer()
        recognizer.dynamic_energy_threshold = True
        recognizer.pause_threshold = 0.6

        while not self._stop.is_set():
            try:
                with sr.Microphone() as source:
                    recognizer.adjust_for_ambient_noise(source, duration=0.25)
                    audio = recognizer.listen(source, timeout=5, phrase_time_limit=6)
                text = transcribe_audio(recognizer, audio)
                if not text:
                    continue
                text = text.lower().strip()
            except Exception:
                continue

            self.heard_text.emit(text)
            command = match_spoken_command(text, self._phrase_map)
            if command:
                logger.info("Voice command: %s (%s)", command, text)
                self.command_recognized.emit(command, text)
