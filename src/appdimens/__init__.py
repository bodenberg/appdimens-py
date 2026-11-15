"""AppDimens for Python — sizes that look right on every screen.

>>> import appdimens as ad
>>> ad.set_metrics(ad.DimenMetrics(width=600, height=1024))
True
>>> ad.sdp(16)        # scaled, smallest side
32.0
>>> round(ad.asdp(16), 2)  # auto: linear on phones, logarithmic past 480
27.75

Every family token works as a module attribute: ``ad.hdp``, ``ad.wsp``, ``ad.asdpa``,
``ad.logssp``, ``ad.sdpPxiaPh`` … (grammar
``<prefix><s|h|w><dp|sp|em>[Px][a|i|ia][Ph|Lh|Pw|Lw][a|i|ia][Px]``). Same names, same math as
Android, iOS, Flutter, React Native, Web, .NET, GTK, Qt and LVGL.
"""

from ._core import *  # noqa: F401,F403
from ._core import __all__ as _core_all
from ._runtime import Dimens, parse_token, TokenSpec, KIND_DP, KIND_SP, KIND_EM
from . import units, resize, custom  # noqa: F401

__version__ = VERSION  # noqa: F405

_default = Dimens()


def default_scope():
    """The process-wide default :class:`Dimens` scope used by module-level tokens."""
    return _default


def set_metrics(metrics):
    """Publishes a new snapshot on the default scope (returns True when it changed)."""
    return _default.set_metrics(metrics)


def update(**changes):
    """``appdimens.update(width=1280, height=720, density=2)`` on the default scope."""
    return _default.update(**changes)


def metrics():
    return _default.metrics


def add_listener(callback):
    return _default.add_listener(callback)


def dimen(expr):
    """``dimen("16sdp")`` / ``dimen("14assp")`` / ``dimen("10spaceW")`` / ``dimen("5mm")``."""
    return _default(expr)


def resolve(value, **kw):
    return _default.resolve(value, **kw)


def space_w(p):
    return _default.space_w(p)


def space_h(p):
    return _default.space_h(p)


def space_sw(p):
    return _default.space_sw(p)


# Explicit, IDE-discoverable core names (all others resolve through __getattr__).
_EXPLICIT = []
for _p in ("", "a", "p", "pw", "f", "i", "log", "dg", "pr", "ft", "fl", "d"):
    for _ax in ("s", "h", "w"):
        for _k in ("dp", "sp", "em"):
            for _suf in ("", "a", "i", "ia", "Px"):
                _name = _p + _ax + _k + _suf
                globals()[_name] = _default.fn(_name)
                _EXPLICIT.append(_name)
del _p, _ax, _k, _suf, _name


def __getattr__(name):  # PEP 562 — any other token, e.g. sdpPh, hdpLwa, sdpPxiaPh
    if name.startswith("_"):
        raise AttributeError(name)
    try:
        fn = _default.fn(name)
    except ValueError:
        raise AttributeError("module 'appdimens' has no attribute %r" % name)
    globals()[name] = fn
    return fn


__all__ = list(_core_all) + [
    "Dimens", "parse_token", "TokenSpec", "KIND_DP", "KIND_SP", "KIND_EM", "units", "resize", "custom",
    "default_scope", "set_metrics", "update", "metrics", "add_listener", "dimen", "resolve",
    "space_w", "space_h", "space_sw",
] + _EXPLICIT
