from __future__ import annotations

"""Dual-hand 3D wireframe AR effect — live camera with hand mesh overlay."""

from gesturevision.core.types import BGRImage, EffectContext
from gesturevision.effects.compositor import apply_processor
from gesturevision.effects.interactive.base import InteractiveEffect
from gesturevision.effects.interactive.hand_mesh_renderer import draw_dual_hand_mesh


class HandMeshEffect(InteractiveEffect):
    """Passthrough camera feed with LinkedIn-style dual-hand mesh overlay."""

    name = "hand_mesh"
    default_params = {
        "line_color": [80, 200, 120],
        "tip_color": [0, 220, 255],
        "bridge_color": [255, 180, 60],
        "z_scale": 30,
        "mesh_fill_alpha": 0.18,
    }

    def __init__(
        self,
        params: dict | None = None,
        processors: dict | None = None,
    ) -> None:
        super().__init__(params)
        self._processors = processors or {}

    def apply(self, ctx: EffectContext) -> BGRImage:
        base = apply_processor(self._processors, "original", ctx.frame, quality=ctx.quality)
        if not ctx.hands:
            return base

        line_color = tuple(ctx.params.get("line_color", self.default_params["line_color"]))
        tip_color = tuple(ctx.params.get("tip_color", self.default_params["tip_color"]))
        bridge_color = tuple(ctx.params.get("bridge_color", self.default_params["bridge_color"]))
        z_scale = int(ctx.params.get("z_scale", self.default_params["z_scale"]))
        mesh_fill_alpha = float(ctx.params.get("mesh_fill_alpha", self.default_params["mesh_fill_alpha"]))

        output = base.copy()
        draw_dual_hand_mesh(
            output,
            ctx.hands,
            line_color=line_color,  # type: ignore[arg-type]
            tip_color=tip_color,  # type: ignore[arg-type]
            bridge_color=bridge_color,  # type: ignore[arg-type]
            z_scale=z_scale,
            mesh_fill_alpha=mesh_fill_alpha,
        )
        return output
