from __future__ import annotations

"""Logging setup driven by config/logging.yaml."""

import logging
import logging.config
from pathlib import Path
from typing import Any

import yaml

from gesturevision.core.exceptions import ConfigError


def setup_logging(project_root: Path, logging_config: dict[str, Any] | None = None) -> None:
    """
    Configure the logging system from a dict or ``config/logging.yaml``.

    Ensures the logs directory exists before file handlers are created.
    """
    logs_dir = project_root / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    if logging_config is None:
        config_path = project_root / "config" / "logging.yaml"
        if not config_path.is_file():
            raise ConfigError(f"Logging config not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as handle:
            logging_config = yaml.safe_load(handle) or {}

    # Rewrite relative log file paths to be absolute under project_root
    handlers = logging_config.get("handlers", {})
    for handler in handlers.values():
        filename = handler.get("filename")
        if filename and not Path(filename).is_absolute():
            handler["filename"] = str(project_root / filename)

    logging.config.dictConfig(logging_config)
    logging.getLogger(__name__).debug("Logging configured")


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger under the gesturevision hierarchy."""
    if name.startswith("gesturevision"):
        return logging.getLogger(name)
    return logging.getLogger(f"gesturevision.{name}")
