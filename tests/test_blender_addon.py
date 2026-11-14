"""Exercises the Blender add-on and helpers against a minimal fake ``bpy`` (no Blender needed)."""
import importlib
import os
import sys
import types

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class _Obj(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)


@pytest.fixture()
def fake_bpy(monkeypatch):
    registered = []
    handlers = []
    bpy = types.ModuleType("bpy")
    props = types.SimpleNamespace(**{n: (lambda **kw: ("prop", kw)) for n in
                                     ("FloatProperty", "EnumProperty", "BoolProperty", "IntProperty", "PointerProperty")})
    space = type("SpaceView3D", (), {
        "draw_handler_add": staticmethod(lambda f, a, r, t: handlers.append(f) or "H"),
        "draw_handler_remove": staticmethod(lambda h, r: handlers.clear()),
    })
    bpy.types = types.SimpleNamespace(PropertyGroup=object, Operator=object, Panel=object,
                                      Scene=type("Scene", (), {}), SpaceView3D=space)
    bpy.props = props
    bpy.utils = types.SimpleNamespace(register_class=registered.append,
                                      unregister_class=registered.remove)
    bpy.app = types.SimpleNamespace(version=(4, 2, 0))
    prefs = _Obj(system=_Obj(ui_scale=2.0), view=_Obj(ui_scale=2.0))
    bpy.context = _Obj(preferences=prefs, region=None)
    monkeypatch.setitem(sys.modules, "bpy", bpy)
    monkeypatch.syspath_prepend(os.path.join(ROOT, "blender"))
    return bpy, registered, handlers


def test_helpers(fake_bpy):
    from appdimens.integrations import blender as b
    region = _Obj(width=1200, height=1600, as_pointer=lambda: 7)
    m = b.metrics_from_region(region)
    assert (m.width, m.height, m.density) == (600, 800, 2.0)
    scene = _Obj(render=_Obj(resolution_x=3840, resolution_y=2160, resolution_percentage=50,
                             pixel_aspect_x=1, pixel_aspect_y=1))
    r = b.scope_for_render(scene)
    assert (r.metrics.width, r.metrics.height) == (1920, 1080)
    scopes = b.RegionScopes()
    s1 = scopes.get(region)
    assert scopes.get(region) is s1
    region.width = 2400
    assert scopes.get(region).metrics.width == 1200


def test_addon_register_cycle(fake_bpy):
    bpy, registered, handlers = fake_bpy
    sys.modules.pop("appdimens_blender", None)
    addon = importlib.import_module("appdimens_blender")
    assert addon.bl_info["blender"] == (2, 80, 0)
    addon.register()
    assert len(registered) == 3 and hasattr(bpy.types.Scene, "appdimens")
    addon._toggle_overlay(True)
    assert handlers
    addon.unregister()
    assert not registered and not handlers
    region = _Obj(width=600, height=1066, as_pointer=lambda: 1)
    assert addon.region_dimens(region).sdp(16) == pytest.approx(16.0)
