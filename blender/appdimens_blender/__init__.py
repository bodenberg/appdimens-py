# SPDX-License-Identifier: Apache-2.0
"""AppDimens for Blender — responsive sizes for add-on UI, viewport overlays and render text.

Works as a legacy add-on (Blender 2.80 → 4.1, uses ``bl_info``) and as an Extension
(Blender 4.2+, uses ``blender_manifest.toml``). The ``appdimens`` package is vendored in
``vendor/`` by ``scripts/build_blender_addon.py`` so the add-on has no pip dependency.

Python API for other add-ons::

    from appdimens_blender import region_dimens, render_dimens
    d = region_dimens(context.region)      # UI units, follows Resolution Scale + monitor DPI
    blf.size(0, d.ssp(13))                 # text that keeps proportion on any monitor
    r = render_dimens(context.scene)       # output resolution (1080p → 4K → 9:16)
    text_obj.data.size = r.sdp(0.1)        # same visual size in every delivery format
"""

bl_info = {
    "name": "AppDimens",
    "author": "Jean Bodenberg",
    "version": (3, 2, 0),
    "blender": (2, 80, 0),
    "location": "3D Viewport ▸ Sidebar ▸ AppDimens",
    "description": "Responsive sizing (sdp/ssp/asdp…) for add-on UI, overlays and render-relative text",
    "doc_url": "https://github.com/bodenberg/appdimens-py/blob/main/docs/BLENDER.md",
    "tracker_url": "https://github.com/bodenberg/appdimens-py/issues",
    "category": "Interface",
}

try:  # vendored copy (release zip)
    from .vendor import appdimens  # type: ignore
except ImportError:  # development: installed with pip
    import appdimens  # type: ignore

import bpy  # noqa: E402

from importlib import import_module  # noqa: E402

_blender = import_module(appdimens.__name__ + ".integrations.blender")

_scopes = _blender.RegionScopes()
_draw_handle = None


def region_dimens(region, context=None):
    """Live :class:`appdimens.Dimens` for a UI region (cached, cheap every frame)."""
    return _scopes.get(region, context)


def render_dimens(scene):
    """:class:`appdimens.Dimens` for the scene's final render resolution."""
    return _blender.scope_for_render(scene)


TOKENS = [(t, t, "") for t in ("sdp", "asdp", "ssp", "assp", "hdp", "wdp", "pwsdp", "logsdp",
                                 "fsdp", "ftsdp", "flsdp", "dgsdp", "sdpa", "sdpPx")]


class APPDIMENS_Props(bpy.types.PropertyGroup):
    value: bpy.props.FloatProperty(name="Value", default=16.0, min=0.0)
    token: bpy.props.EnumProperty(name="Token", items=TOKENS, default="sdp")
    overlay: bpy.props.BoolProperty(name="Viewport overlay", default=False,
                                    update=lambda self, ctx: _toggle_overlay(self.overlay))
    ref_x: bpy.props.IntProperty(name="Reference width", default=1920, min=1)
    ref_y: bpy.props.IntProperty(name="Reference height", default=1080, min=1)


class APPDIMENS_OT_scale_text(bpy.types.Operator):
    """Rescale selected text objects from the reference resolution to the current render resolution"""
    bl_idname = "appdimens.scale_text_to_render"
    bl_label = "Fit Text to Render"
    bl_options = {"REGISTER", "UNDO"}

    token: bpy.props.EnumProperty(name="Strategy", items=TOKENS, default="asdp")

    def execute(self, context):
        p = context.scene.appdimens
        cur = render_dimens(context.scene)
        ref = appdimens.Dimens(appdimens.DimenMetrics(width=p.ref_x, height=p.ref_y))
        f_cur, f_ref = cur.fn(self.token)(1.0), ref.fn(self.token)(1.0)
        ratio = f_cur / f_ref if f_ref else 1.0
        n = 0
        for ob in context.selected_objects:
            if ob.type == "FONT":
                ob.data.size *= ratio
                n += 1
        self.report({"INFO"}, "AppDimens: %d text object(s) × %.4f" % (n, ratio))
        return {"FINISHED"}


class APPDIMENS_PT_panel(bpy.types.Panel):
    bl_label = "AppDimens"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "AppDimens"

    def draw(self, context):
        layout = self.layout
        p = context.scene.appdimens
        d = region_dimens(context.region, context)
        m = d.metrics
        col = layout.column(align=True)
        col.label(text="Region: %.0f × %.0f  (scale %.2f)" % (m.width, m.height, m.density))
        col.prop(p, "value")
        col.prop(p, "token")
        col.label(text="UI: %s(%g) = %.2f" % (p.token, p.value, d.fn(p.token)(p.value)))
        r = render_dimens(context.scene)
        col.label(text="Render %.0f × %.0f: %.2f" % (r.metrics.width, r.metrics.height,
                                                    r.fn(p.token)(p.value)))
        layout.separator()
        box = layout.box()
        box.label(text="Render-relative text")
        row = box.row(align=True)
        row.prop(p, "ref_x")
        row.prop(p, "ref_y")
        box.operator(APPDIMENS_OT_scale_text.bl_idname)
        layout.prop(p, "overlay")


def _draw_overlay():
    import blf
    ctx = bpy.context
    region = ctx.region
    if region is None:
        return
    d = region_dimens(region, ctx)
    font = 0
    _blender.blf_size(font, d.sspPx(14))
    pad = d.sdpPx(12)
    blf.position(font, pad, pad, 0)
    blf.draw(font, "AppDimens · %s = %.1f px" % ("sspPx(14)", d.sspPx(14)))


def _toggle_overlay(enabled):
    global _draw_handle
    if enabled and _draw_handle is None:
        _draw_handle = bpy.types.SpaceView3D.draw_handler_add(_draw_overlay, (), "WINDOW", "POST_PIXEL")
    elif not enabled and _draw_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(_draw_handle, "WINDOW")
        _draw_handle = None


CLASSES = (APPDIMENS_Props, APPDIMENS_OT_scale_text, APPDIMENS_PT_panel)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)
    bpy.types.Scene.appdimens = bpy.props.PointerProperty(type=APPDIMENS_Props)


def unregister():
    _toggle_overlay(False)
    _scopes.clear()
    del bpy.types.Scene.appdimens
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)
