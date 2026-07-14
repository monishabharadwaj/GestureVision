from __future__ import annotations

"""YAML configuration loading with path resolution."""

import logging
from pathlib import Path
from typing import Any

import yaml

from gesturevision.core.exceptions import ConfigError

logger = logging.getLogger(__name__)


def find_project_root(start: Path | None = None) -> Path:
    """
    Walk upward from ``start`` (or this file) until a directory containing
    ``config/app.yaml`` is found.
    """
    current = (start or Path(__file__).resolve()).parent
    for candidate in [current, *current.parents]:
        if (candidate / "config" / "app.yaml").is_file():
            return candidate
    raise ConfigError("Could not locate project root (config/app.yaml missing).")


class ConfigLoader:
    """Loads and merges YAML configuration files from the config directory."""

    def __init__(self, project_root: Path | None = None) -> None:
        self.project_root = project_root or find_project_root()
        self.config_dir = self.project_root / "config"
        self._cache: dict[str, dict[str, Any]] = {}

    def load(self, name: str, *, reload: bool = False) -> dict[str, Any]:
        """
        Load a configuration file by stem name (e.g. ``\"app\"`` → ``app.yaml``).

        Results are cached unless ``reload`` is True.
        """
        if not reload and name in self._cache:
            return self._cache[name]

        path = self.config_dir / f"{name}.yaml"
        if not path.is_file():
            raise ConfigError(f"Configuration file not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as handle:
                data = yaml.safe_load(handle) or {}
        except yaml.YAMLError as exc:
            raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
        except OSError as exc:
            raise ConfigError(f"Unable to read {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise ConfigError(f"Configuration root must be a mapping: {path}")

        self._cache[name] = data
        logger.debug("Loaded config: %s", path)
        return data

    def load_all(self, *, reload: bool = False) -> dict[str, dict[str, Any]]:
        """Load all known configuration sections used by the application."""
        sections = ("app", "camera", "gestures", "effects", "logging", "accessibility")
        return {name: self.load(name, reload=reload) for name in sections}

    def resolve_path(self, relative: str | Path) -> Path:
        """Resolve a path relative to the project root."""
        path = Path(relative)
        if path.is_absolute():
            return path
        return (self.project_root / path).resolve()

    def clear_cache(self) -> None:
        """Drop cached configuration documents."""
        self._cache.clear()
