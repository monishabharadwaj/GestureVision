from __future__ import annotations

"""Effect plugin registry and factory."""

import logging
from typing import Any

from gesturevision.effects.base import BaseEffect
from gesturevision.effects.classical.blur import BlurEffect
from gesturevision.effects.classical.edge import EdgeEffect
from gesturevision.effects.classical.original import OriginalEffect
from gesturevision.effects.classical.sketch import SketchEffect
from gesturevision.effects.interactive.image_reveal import ImageRevealEffect
from gesturevision.effects.interactive.virtual_brush import VirtualBrushEffect

logger = logging.getLogger(__name__)

_CLASSICAL_EFFECTS: dict[str, type[BaseEffect]] = {
    "original": OriginalEffect,
    "sketch": SketchEffect,
    "blur": BlurEffect,
    "edge": EdgeEffect,
}

_INTERACTIVE_EFFECTS: dict[str, type[BaseEffect]] = {
    "brush": VirtualBrushEffect,
    "reveal": ImageRevealEffect,
}


def available_effect_types() -> dict[str, type[BaseEffect]]:
    return {**_CLASSICAL_EFFECTS, **_INTERACTIVE_EFFECTS}


def build_effects_from_config(config: dict[str, Any]) -> dict[str, BaseEffect]:
    """
    Instantiate enabled effects declared in ``effects.yaml``.

    Classical effects are built first so interactive modes can compose them.
    """
    effects_cfg = config.get("effects", config)
    registry = effects_cfg.get("registry", [])
    built: dict[str, BaseEffect] = {}

    for entry in registry:
        name = str(entry.get("name", "")).lower()
        if not entry.get("enabled", True):
            logger.debug("Effect disabled in config: %s", name)
            continue

        effect_cls = _CLASSICAL_EFFECTS.get(name)
        if effect_cls is None:
            continue

        params = entry.get("params", {})
        built[name] = effect_cls(params=params)
        logger.debug("Registered classical effect: %s", name)

    if "original" not in built:
        built["original"] = OriginalEffect()

    processors = dict(built)

    for entry in registry:
        name = str(entry.get("name", "")).lower()
        if not entry.get("enabled", True):
            continue

        effect_cls = _INTERACTIVE_EFFECTS.get(name)
        if effect_cls is None:
            if name not in _CLASSICAL_EFFECTS:
                logger.warning("Unknown effect in registry: %s", name)
            continue

        params = entry.get("params", {})
        built[name] = effect_cls(params=params, processors=processors)
        logger.debug("Registered interactive effect: %s", name)

    return built
