from __future__ import annotations

"""On-screen gesture menu for Dandelion app navigation."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GestureMenuController:
    """Cycle and select launch targets without keyboard or mouse."""

    items: list[str] = field(default_factory=list)
    apps_config: dict[str, Any] = field(default_factory=dict)
    open: bool = False
    index: int = 0

    def open_menu(self) -> str:
        self.open = True
        self.index = 0
        return self.current_label()

    def next_item(self) -> str:
        if not self.open or not self.items:
            return ""
        self.index = (self.index + 1) % len(self.items)
        return self.current_label()

    def select(self) -> tuple[str, str] | None:
        if not self.open or not self.items:
            return None
        app_id = self.items[self.index]
        label = self.label_for(app_id)
        self.open = False
        return app_id, label

    def close(self) -> None:
        self.open = False

    def current_label(self) -> str:
        if not self.items:
            return ""
        return self.label_for(self.items[self.index])

    def label_for(self, app_id: str) -> str:
        apps = self.apps_config.get("apps", self.apps_config)
        entry = apps.get(app_id, {})
        return str(entry.get("label", app_id.replace("_", " ").title()))

    def all_labels(self) -> list[str]:
        return [self.label_for(item) for item in self.items]
