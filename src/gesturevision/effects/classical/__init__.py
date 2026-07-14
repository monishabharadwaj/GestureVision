"""Classical OpenCV-based effects."""

from gesturevision.effects.classical.blur import BlurEffect
from gesturevision.effects.classical.edge import EdgeEffect
from gesturevision.effects.classical.original import OriginalEffect
from gesturevision.effects.classical.sketch import SketchEffect

__all__ = ["OriginalEffect", "SketchEffect", "BlurEffect", "EdgeEffect"]
