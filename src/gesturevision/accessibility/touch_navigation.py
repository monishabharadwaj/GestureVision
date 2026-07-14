from __future__ import annotations

"""Finger-as-touchscreen navigation for Dandelion mode."""

from dataclasses import dataclass, field
import time


@dataclass(slots=True)
class TouchZone:
    app_id: str
    label: str
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class TouchNavigator:
    """Map finger position to on-screen zones; pinch to tap like a touchscreen."""

    zones: list[TouchZone] = field(default_factory=list)
    hover_id: str | None = None
    dwell_seconds: float = 0.55
    _hover_since: float | None = None
    _last_tap_at: float = 0.0
    tap_cooldown: float = 1.2

    def zone_at(self, norm_x: float, norm_y: float) -> TouchZone | None:
        x = max(0.0, min(1.0, norm_x))
        y = max(0.0, min(1.0, norm_y))
        for zone in self.zones:
            if zone.x1 <= x <= zone.x2 and zone.y1 <= y <= zone.y2:
                return zone
        return None

    def update(
        self,
        norm_x: float | None,
        norm_y: float | None,
        *,
        pointing: bool,
        pinching: bool,
    ) -> tuple[str | None, str | None]:
        """
        Returns (hover_app_id, tap_app_id).
        Tap triggers on pinch while hovering, or after dwell while pointing.
        """
        if norm_x is None or norm_y is None:
            self.hover_id = None
            self._hover_since = None
            return None, None

        zone = self.zone_at(norm_x, norm_y)
        hover = zone.app_id if zone else None
        self.hover_id = hover

        now = time.perf_counter()
        if hover is None:
            self._hover_since = None
            return None, None

        if self._hover_since is None or self.hover_id != hover:
            self._hover_since = now

        tap_id: str | None = None
        if now - self._last_tap_at < self.tap_cooldown:
            return hover, None

        dwell_ready = (now - (self._hover_since or now)) >= self.dwell_seconds
        if pinching or (pointing and dwell_ready):
            tap_id = hover
            self._last_tap_at = now
            self._hover_since = None

        return hover, tap_id


def zones_from_app_ids(app_ids: list[str], apps: dict) -> list[TouchZone]:
    """Build a bottom touch bar with one zone per app."""
    if not app_ids:
        return []

    count = len(app_ids)
    width = 1.0 / count
    zones: list[TouchZone] = []
    for index, app_id in enumerate(app_ids):
        entry = apps.get(app_id, {})
        label = str(entry.get("label", app_id.title()))
        zones.append(
            TouchZone(
                app_id=app_id,
                label=label,
                x1=index * width,
                y1=0.82,
                x2=(index + 1) * width,
                y2=0.98,
            )
        )
    return zones
