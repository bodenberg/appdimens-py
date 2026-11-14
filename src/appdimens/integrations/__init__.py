"""Adapters that build :class:`~appdimens.DimenMetrics` from popular Python toolkits.

All adapters are duck-typed: importing this module never imports a GUI toolkit. Each
``metrics_from_*`` returns a snapshot; each ``bind_*`` keeps a :class:`~appdimens.Dimens`
scope updated on resize / DPI change and returns an ``unbind`` function.

Covered: raw pixels, Tkinter, Qt for Python (PySide6/PySide2/PyQt6/PyQt5), Kivy, pygame /
pygame-ce, pyglet / arcade, wxPython, Dear PyGui, Panda3D / Ursina, Blender (UI regions and
render output). See ``appdimens.integrations.blender`` for the Blender-specific helpers.
"""

from .._core import DimenMetrics, UiModeType

__all__ = [
    "metrics_from_pixels", "metrics_from_tk", "bind_tk", "metrics_from_qt", "metrics_from_kivy",
    "bind_kivy", "metrics_from_pygame", "metrics_from_pyglet", "metrics_from_wx",
    "metrics_from_dearpygui", "metrics_from_panda3d",
]


def metrics_from_pixels(width_px, height_px, density=1.0, font_scale=1.0, dpi=None,
                        multi_window=False, ui_mode=UiModeType.NORMAL):
    """Physical pixels + device scale → logical snapshot (``width = width_px / density``)."""
    density = float(density) if density and density > 0 else 1.0
    return DimenMetrics(width=width_px / density, height=height_px / density, density=density,
                        font_scale=font_scale, dpi=dpi, multi_window=multi_window, ui_mode=ui_mode)


# ── Tkinter ─────────────────────────────────────────────────────────────────────────────
def metrics_from_tk(widget, font_scale=1.0):
    """Tk: pixels per point (``tk scaling``) → density relative to 96 dpi."""
    widget.update_idletasks()
    ppp = float(widget.tk.call("tk", "scaling"))  # pixels per typographic point
    dpi = ppp * 72.0
    density = dpi / 96.0
    w = widget.winfo_width() or widget.winfo_reqwidth()
    h = widget.winfo_height() or widget.winfo_reqheight()
    return metrics_from_pixels(w, h, density, font_scale, dpi=dpi)


def bind_tk(widget, scope, font_scale=1.0):
    """Updates ``scope`` on every ``<Configure>`` of ``widget``."""
    def on_configure(_event=None):
        scope.set_metrics(metrics_from_tk(widget, font_scale))
    funcid = widget.bind("<Configure>", on_configure, add="+")
    on_configure()
    return lambda: widget.unbind("<Configure>", funcid)


# ── Qt for Python ───────────────────────────────────────────────────────────────────────
def metrics_from_qt(obj, use_available_geometry=False, font_scale=None):
    """Accepts a ``QWidget``/``QWindow`` (uses its size + screen) or a ``QScreen``.

    Qt geometry is already in logical pixels; ``devicePixelRatio`` is the density.
    """
    screen = obj
    width = height = None
    if hasattr(obj, "screen") and callable(getattr(obj, "screen")):
        screen = obj.screen()
        size = obj.size()
        width, height = size.width(), size.height()
    if screen is None:
        raise ValueError("object has no screen yet (call after show())")
    if width is None:
        g = screen.availableGeometry() if use_available_geometry else screen.geometry()
        width, height = g.width(), g.height()
    dpr = float(screen.devicePixelRatio())
    dpi = float(screen.physicalDotsPerInch()) if hasattr(screen, "physicalDotsPerInch") else None
    if font_scale is None:
        font_scale = 1.0
    return DimenMetrics(width=width, height=height, density=dpr, font_scale=font_scale, dpi=dpi)


# ── Kivy ────────────────────────────────────────────────────────────────────────────────
def metrics_from_kivy(window=None):
    if window is None:
        from kivy.core.window import Window as window  # noqa: N813
    from kivy.metrics import Metrics
    return metrics_from_pixels(window.width, window.height, Metrics.density,
                               getattr(Metrics, "fontscale", 1.0), dpi=getattr(Metrics, "dpi", None))


def bind_kivy(scope, window=None):
    if window is None:
        from kivy.core.window import Window as window  # noqa: N813

    def on_resize(*_a):
        scope.set_metrics(metrics_from_kivy(window))
    window.bind(on_resize=on_resize)
    on_resize()
    return lambda: window.unbind(on_resize=on_resize)


# ── Game / multimedia toolkits ───────────────────────────────────────────────────────────
def metrics_from_pygame(surface_or_size, density=1.0, font_scale=1.0):
    """pygame / pygame-ce: ``pygame.display.get_surface()`` or a ``(w, h)`` tuple in pixels.

    With ``pygame.SCALED`` / HiDPI windows pass ``density = drawable_w / window_w``.
    """
    if hasattr(surface_or_size, "get_size"):
        w, h = surface_or_size.get_size()
    else:
        w, h = surface_or_size
    return metrics_from_pixels(w, h, density, font_scale)


def metrics_from_pyglet(window, font_scale=1.0):
    """pyglet / arcade windows (``get_size`` is logical, ``get_pixel_ratio`` the density)."""
    w, h = window.get_size()
    ratio = float(window.get_pixel_ratio()) if hasattr(window, "get_pixel_ratio") else 1.0
    return DimenMetrics(width=w, height=h, density=ratio, font_scale=font_scale)


def metrics_from_wx(window, font_scale=1.0):
    size = window.GetClientSize()
    scale = 1.0
    for attr in ("GetDPIScaleFactor", "GetContentScaleFactor"):
        if hasattr(window, attr):
            scale = float(getattr(window, attr)())
            break
    # wx client size is in logical (DIP) units on macOS/GTK and physical px on MSW;
    # FromDIP/ToDIP normalise it when available.
    if hasattr(window, "ToDIP"):
        size = window.ToDIP(size)
    return DimenMetrics(width=size.GetWidth(), height=size.GetHeight(), density=scale, font_scale=font_scale)


def metrics_from_dearpygui(dpg=None, density=1.0, font_scale=1.0):
    if dpg is None:
        import dearpygui.dearpygui as dpg
    return metrics_from_pixels(dpg.get_viewport_client_width(), dpg.get_viewport_client_height(),
                               density, font_scale)


def metrics_from_panda3d(base=None, density=1.0, font_scale=1.0):
    """Panda3D / Ursina: ``base.win`` size in pixels."""
    if base is None:
        import builtins
        base = builtins.base  # Panda3D ShowBase global
    win = base.win
    return metrics_from_pixels(win.getXSize(), win.getYSize(), density, font_scale)
