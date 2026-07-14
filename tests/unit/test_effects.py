from __future__ import annotations

"""Unit tests for the effect engine and classical filters."""

import numpy as np

from gesturevision.core.types import EffectContext
from gesturevision.effects.classical.blur import BlurEffect
from gesturevision.effects.classical.edge import EdgeEffect
from gesturevision.effects.classical.sketch import SketchEffect
from gesturevision.effects.engine import EffectEngine


def _solid_frame(color: tuple[int, int, int] = (40, 120, 200)) -> np.ndarray:
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    frame[:, :] = color
    return frame


def _effects_config() -> dict:
    return {
        "effects": {
            "default": "original",
            "quality_tier": "preview",
            "registry": [
                {"name": "original", "enabled": True},
                {"name": "sketch", "enabled": True},
                {"name": "blur", "enabled": True, "params": {"strength": 7}},
                {"name": "edge", "enabled": True},
            ],
        }
    }


def test_effect_engine_switches_active_effect() -> None:
    engine = EffectEngine(_effects_config())
    assert engine.active_effect == "original"
    assert engine.set_active_effect("sketch") is True
    assert engine.active_effect == "sketch"


def test_sketch_changes_pixels() -> None:
    frame = _solid_frame()
    result = SketchEffect().apply(EffectContext(frame=frame))
    assert result.shape == frame.shape
    assert not np.array_equal(result, frame)


def test_blur_softens_image() -> None:
    frame = _solid_frame()
    frame[40:80, 60:100] = (255, 255, 255)
    result = BlurEffect({"strength": 15}).apply(EffectContext(frame=frame))
    # Edge of the white patch should blend with the blue background.
    assert int(result[40, 60, 0]) != int(frame[40, 60, 0])


def test_edge_produces_high_contrast() -> None:
    frame = _solid_frame()
    frame[:, 80:] = (10, 10, 10)
    result = EdgeEffect().apply(EffectContext(frame=frame))
    assert int(result.max()) == 255


def test_engine_adjusts_blur_strength() -> None:
    engine = EffectEngine(_effects_config())
    engine.set_active_effect("blur")
    engine.adjust_active_parameter("strength", 1.0)
    blur = engine.get_effect("blur")
    assert blur is not None
    assert int(blur.params["strength"]) >= 31
