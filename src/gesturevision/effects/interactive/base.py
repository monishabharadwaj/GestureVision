from __future__ import annotations

"""Base class for finger-driven interactive effects."""

from gesturevision.effects.base import BaseEffect


class InteractiveEffect(BaseEffect):
    """Interactive effects may persist state across frames."""

    def reset(self) -> None:
        """Clear per-session state when switching away from this effect."""
