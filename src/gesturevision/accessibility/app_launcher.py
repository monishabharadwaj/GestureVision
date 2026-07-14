from __future__ import annotations

"""Launch external apps for Dandelion gesture navigation."""

import logging
import os
import shutil
import subprocess
import webbrowser
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_WINDOWS_CHROME_PATHS = (
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path.home() / "AppData" / "Local" / "Google" / "Chrome" / "Application" / "chrome.exe",
)


def launch_url(url: str) -> None:
    """Open any URL in the default browser."""
    if _open_url(url):
        logger.info("Opened URL: %s", url)
        return
    webbrowser.open(url, new=2)
    logger.info("Opened URL via browser: %s", url)


def launch_app(app_id: str, apps_config: dict[str, Any]) -> str:
    """Open a configured app or URL. Returns a human-readable label."""
    normalized = app_id.strip().lower()
    apps = apps_config.get("apps", apps_config)

    if normalized in {"brush", "paint"}:
        return "Paint"

    entry = apps.get(normalized, {})
    label = str(entry.get("label", normalized.title()))
    url = str(entry.get("url", ""))

    if url:
        launch_url(url)
        return label

    raise ValueError(f"Unknown or misconfigured app: {app_id}")


def _open_url(url: str) -> bool:
    if os.name == "nt":
        try:
            os.startfile(url)  # noqa: S606 — Windows opens default browser reliably
            return True
        except OSError:
            pass

    chrome = shutil.which("chrome") or shutil.which("google-chrome")
    if chrome:
        subprocess.Popen([chrome, "--new-tab", url], close_fds=True)
        return True

    for path in _WINDOWS_CHROME_PATHS:
        if path.is_file():
            subprocess.Popen([str(path), "--new-tab", url], close_fds=True)
            return True
    return False
