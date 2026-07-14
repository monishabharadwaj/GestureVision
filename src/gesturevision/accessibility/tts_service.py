from __future__ import annotations

"""Text-to-speech for Beauty (blind) mode."""

import logging
import queue
import threading
from typing import Any

logger = logging.getLogger(__name__)


class TextToSpeechService:
    """Queue-based offline speech using pyttsx3 when available."""

    def __init__(self) -> None:
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._engine: Any = None
        self._available = False
        self._running = False

    @property
    def available(self) -> bool:
        return self._available

    def start(self) -> None:
        if self._running:
            return
        try:
            import pyttsx3

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", 165)
            self._available = True
        except Exception:
            logger.warning("TTS unavailable — install pyttsx3 for Beauty mode voice", exc_info=True)
            self._available = False
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker, name="TTSService", daemon=True)
        self._thread.start()

    def speak(self, text: str) -> None:
        if not text.strip() or not self._available:
            return
        self._queue.put(text.strip())

    def shutdown(self) -> None:
        if not self._running:
            return
        self._queue.put(None)
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._running = False
        self._engine = None
        self._available = False

    def _worker(self) -> None:
        while True:
            text = self._queue.get()
            if text is None:
                break
            try:
                if self._engine is not None:
                    self._engine.say(text)
                    self._engine.runAndWait()
            except Exception:
                logger.exception("TTS failed for: %s", text)
