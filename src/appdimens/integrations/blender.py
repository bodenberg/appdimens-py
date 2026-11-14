"""Blender helpers (2.80 → 4.x / 5.x). Pure Python, imported lazily from add-ons.

Two families of snapshots:

* **UI** — ``metrics_from_region(region)``: the region size in Blender UI units
  (pixels ÷ ``preferences.system.ui_scale``) with ``density = ui_scale``. Use it for
  ``blf`` text, ``gpu`` overlays, gizmos and ``layout.scale_x/scale_y`` so custom UI keeps
  proportion on laptops, 4K monitors and ultrawides.
* **Render** — ``metrics_from_render(scene)``: the final output resolution (respecting
  ``resolution_percentage`` and pixel aspect) with ``density = 1``. Use it for burn-ins,
  lower-thirds, title text objects and compositor overlays that must keep proportion from a
  1080p preview to a 4K/8K or vertical 9:16 delivery.
"""

from .._core import DimenMetrics, UiModeType
from .._runtime import Dimens

__all__ = ["ui_scale", "metrics_from_region", "metrics_from_render", "scope_for_region",
           "scope_for_render", "blf_size", "layout_scale", "RegionScopes"]


def _prefs(context=None):
    if context is None:
        import bpy
        context = bpy.context
    return context.preferences


def ui_scale(context=None):
    """Effective UI scale (``preferences.system.ui_scale``: resolution scale × DPI × pixel size)."""
    try:
        s = float(_prefs(context).system.ui_scale)
    except Exception:  # pragma: no cover - very old builds
        s = float(getattr(_prefs(context).view, "ui_scale", 1.0))
    return s if s > 0 else 1.0


def metrics_from_region(region, context=None, font_scale=1.0):
    s = ui_scale(context)
    return DimenMetrics(width=region.width / s, height=region.height / s, density=s,
                        font_scale=font_scale, ui_mode=UiModeType.DESK)


def metrics_from_render(scene, include_percentage=True):
    r = scene.render
    pct = (r.resolution_percentage / 100.0) if include_percentage else 1.0
    w = r.resolution_x * pct
    h = r.resolution_y * pct
    aspect_x = float(getattr(r, "pixel_aspect_x", 1.0) or 1.0)
    aspect_y = float(getattr(r, "pixel_aspect_y", 1.0) or 1.0)
    w *= aspect_x / aspect_y  # display aspect for anamorphic outputs
    return DimenMetrics(width=w, height=h, density=1.0)


def scope_for_region(region, context=None):
    return Dimens(metrics_from_region(region, context))


def scope_for_render(scene):
    return Dimens(metrics_from_render(scene))


def blf_size(font_id, size_px, dpi=None):
    """Version-safe ``blf.size`` (the ``dpi`` argument was removed in Blender 4.0)."""
    import blf
    import bpy
    if bpy.app.version >= (4, 0, 0):
        blf.size(font_id, size_px)
    else:  # pragma: no cover
        blf.size(font_id, int(round(size_px)), int(dpi or 72))


def layout_scale(dimens, base=1.0, token="asdp"):
    """Value for ``layout.scale_y``: grows with the region like ``token`` does, from ``base``."""
    return dimens.fn(token)(base)


class RegionScopes(object):
    """Caches one live :class:`Dimens` per region (keyed by ``as_pointer()``).

    Call ``get(context.region)`` inside ``draw`` callbacks: it updates the snapshot only
    when the region size or UI scale changed (one tuple compare), so it is safe to call
    every frame.
    """

    def __init__(self):
        self._scopes = {}

    def get(self, region, context=None):
        key = region.as_pointer() if hasattr(region, "as_pointer") else id(region)
        scope = self._scopes.get(key)
        sig = (region.width, region.height, ui_scale(context))
        if scope is None:
            scope = Dimens(metrics_from_region(region, context))
            self._scopes[key] = scope
            scope._ad_sig = sig  # noqa: SLF001
        elif getattr(scope, "_ad_sig", None) != sig:
            scope.set_metrics(metrics_from_region(region, context))
            scope._ad_sig = sig  # noqa: SLF001
        return scope

    def clear(self):
        self._scopes.clear()
