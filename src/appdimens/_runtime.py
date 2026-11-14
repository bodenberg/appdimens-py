"""Runtime: live scopes, token grammar and O(1) resolvers.

A :class:`Dimens` scope owns one live :class:`DimenMetrics` snapshot (one window, one
Blender region, one game surface…). Resolvers such as ``scope.sdp`` are closures that read
one atomically-published tuple and do one multiply — no locks, no allocation, no parsing
on the hot path. The module-level functions (``appdimens.sdp`` …) use the default scope.
"""

import re
import threading

from ._core import (
    BASE_WIDTH_DP, STRATEGIES, STRATEGY_PREFIX, DimenMetrics, DpQualifier, Inverter,
    Orientation, compute_factor, variant_slot,
)

__all__ = ["Dimens", "parse_token", "TokenSpec", "TOKEN_RE", "KIND_DP", "KIND_SP", "KIND_EM"]

KIND_DP = 0  # layout size
KIND_SP = 1  # text, follows the user's font scale
KIND_EM = 2  # text, ignores the user's font scale

_PREFIXES = sorted([p for p in STRATEGY_PREFIX if p], key=len, reverse=True)
TOKEN_RE = re.compile(
    r"^(?P<prefix>" + "|".join(_PREFIXES) + r")?"
    r"(?P<axis>[shw])(?P<kind>dp|sp|em)"
    r"(?P<px1>Px)?(?P<f1>ia|a|i)?(?P<inv>Ph|Lh|Pw|Lw)?(?P<f2>ia|a|i)?(?P<px2>Px)?$"
)
_NUM_TOKEN_RE = re.compile(r"^\s*(?P<num>[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?)\s*(?P<tok>[A-Za-z]+)\s*$")

_AXIS_Q = {"s": DpQualifier.SMALL_WIDTH, "h": DpQualifier.HEIGHT, "w": DpQualifier.WIDTH}
_INV = {
    ("s", "Ph"): Inverter.SW_TO_PH, ("s", "Lh"): Inverter.SW_TO_LH,
    ("s", "Pw"): Inverter.SW_TO_PW, ("s", "Lw"): Inverter.SW_TO_LW,
    ("h", "Lw"): Inverter.PH_TO_LW, ("h", "Pw"): Inverter.LH_TO_PW,
    ("w", "Lh"): Inverter.PW_TO_LH, ("w", "Ph"): Inverter.LW_TO_PH,
}
_KIND = {"dp": KIND_DP, "sp": KIND_SP, "em": KIND_EM}


class TokenSpec(tuple):
    """Parsed token: ``(strategy, qualifier, inverter, kind, px, ignore_mw, aspect_ratio)``."""
    __slots__ = ()
    strategy = property(lambda s: s[0])
    qualifier = property(lambda s: s[1])
    inverter = property(lambda s: s[2])
    kind = property(lambda s: s[3])
    px = property(lambda s: s[4])
    ignore_multi_window = property(lambda s: s[5])
    aspect_ratio = property(lambda s: s[6])


_SPEC_CACHE = {}


def parse_token(name):
    """Parses a family token (``sdp``, ``asdpa``, ``hdpLw``, ``sdpPxiaPh``, ``logssp`` …).

    Raises :class:`ValueError` for names outside the grammar
    ``<prefix><s|h|w><dp|sp|em>[Px][a|i|ia][Ph|Lh|Pw|Lw][a|i|ia][Px]``.
    """
    spec = _SPEC_CACHE.get(name)
    if spec is not None:
        return spec
    m = TOKEN_RE.match(name)
    if not m or (m.group("f1") and m.group("f2")) or (m.group("px1") and m.group("px2")):
        raise ValueError("not an AppDimens token: %r" % (name,))
    axis = m.group("axis")
    inv_tok = m.group("inv")
    inverter = Inverter.DEFAULT
    if inv_tok:
        inverter = _INV.get((axis, inv_tok))
        if inverter is None:
            raise ValueError("inverter %s is not valid on axis %r in %r" % (inv_tok, axis, name))
    flags = m.group("f1") or m.group("f2") or ""
    spec = TokenSpec((
        STRATEGY_PREFIX.index(m.group("prefix") or ""),
        _AXIS_Q[axis], inverter, _KIND[m.group("kind")],
        bool(m.group("px1") or m.group("px2")), "i" in flags, "a" in flags,
    ))
    _SPEC_CACHE[name] = spec
    return spec


class Dimens(object):
    """A live scaling scope. Thread-safe: updates publish one immutable tuple.

    >>> d = Dimens(DimenMetrics(width=600, height=1024))
    >>> d.sdp(16)
    32.0
    >>> round(d("16asdp"), 2)  # string form, handy in config files / themes
    27.75
    """

    def __init__(self, metrics=None):
        self._lock = threading.Lock()
        self._listeners = []
        self._fns = {}
        self._expr_cache = {}
        self._state = None
        self.set_metrics(metrics if metrics is not None else DimenMetrics())

    # -- state ---------------------------------------------------------------------------
    @property
    def metrics(self):
        return self._state[3]

    def set_metrics(self, metrics):
        """Publishes a new snapshot. Returns True when it changed (listeners are notified)."""
        if not isinstance(metrics, DimenMetrics):
            raise TypeError("expected DimenMetrics")
        old = self._state[3] if self._state else None
        if old is not None and old == metrics:
            return False
        tables = tuple(metrics.table(s) for s in range(len(STRATEGIES)))
        self._state = (tables, metrics.font_scale, metrics.density, metrics)
        for cb in list(self._listeners):
            cb(metrics)
        return True

    def update(self, **changes):
        """``scope.update(width=1280, height=720)`` — keeps the other inputs."""
        cur = self.metrics
        if "orientation" not in changes and ("width" in changes or "height" in changes):
            changes["orientation"] = None
        return self.set_metrics(cur.replace(**changes))

    def add_listener(self, callback):
        """``callback(metrics)`` after every change. Returns a function that removes it."""
        with self._lock:
            self._listeners.append(callback)

        def remove():
            with self._lock:
                if callback in self._listeners:
                    self._listeners.remove(callback)
        return remove

    # -- resolvers -----------------------------------------------------------------------
    def fn(self, name):
        """Returns the O(1) resolver for a token name (cached)."""
        f = self._fns.get(name)
        if f is None:
            f = self._make(parse_token(name))
            f.__name__ = name
            f.__doc__ = "AppDimens %s resolver (value → logical units%s)." % (
                name, "" if not parse_token(name).px else " × density = physical px")
            self._fns[name] = f
        return f

    def _make(self, spec):
        sid, q, inv, kind, px, mw, ar = spec
        slot = variant_slot(q, inv, mw, ar)
        scope = self
        if kind == KIND_SP:
            if px:
                def f(value):
                    st = scope._state
                    return value * st[0][sid][slot] * st[1] * st[2]
            else:
                def f(value):
                    st = scope._state
                    return value * st[0][sid][slot] * st[1]
        else:
            if px:
                def f(value):
                    st = scope._state
                    return value * st[0][sid][slot] * st[2]
            else:
                def f(value):
                    st = scope._state
                    return value * st[0][sid][slot]
        return f

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        try:
            return self.fn(name)
        except ValueError:
            raise AttributeError("%r is neither a Dimens attribute nor an AppDimens token" % name)

    def __call__(self, expr):
        """Resolves ``"16sdp"``, ``"14.5assp"``, ``"10spaceW"``, ``"5mm"`` strings or plain numbers.

        Parsed expressions are cached (bounded), so repeated theme lookups cost one dict hit
        plus one multiply.
        """
        if isinstance(expr, (int, float)):
            return float(expr)
        hit = self._expr_cache.get(expr)
        if hit is None:
            hit = self._compile_expr(expr)
            if len(self._expr_cache) >= 4096:
                self._expr_cache.clear()
            self._expr_cache[expr] = hit
        return hit[1](hit[0])

    def _compile_expr(self, expr):
        m = _NUM_TOKEN_RE.match(expr)
        if not m:
            raise ValueError("cannot parse dimension %r" % (expr,))
        num, tok = float(m.group("num")), m.group("tok")
        scope = self
        if tok in ("dp", "pt"):
            return num, float
        if tok == "px":
            return num, lambda v: v / scope.metrics.density
        if tok in _SPACE:
            return num, getattr(self, _SPACE[tok])
        if tok in ("mm", "cm", "inch", "in"):
            from . import units
            conv = getattr(units, "inch" if tok == "in" else tok)
            return num, lambda v: conv(v, scope.metrics)
        return num, self.fn(tok)

    def resolve(self, value, strategy=0, qualifier=DpQualifier.SMALL_WIDTH, inverter=Inverter.DEFAULT,
                kind=KIND_DP, px=False, ignore_multi_window=False, aspect_ratio=False, k=None):
        """General path (custom sensitivity ``k`` supported)."""
        st = self._state
        m = st[3]
        if k is None:
            slot = variant_slot(qualifier, inverter, ignore_multi_window, aspect_ratio)
            factor = st[0][strategy][slot] if slot >= 0 else compute_factor(
                strategy, m, qualifier, inverter, ignore_multi_window, aspect_ratio)
        else:
            factor = compute_factor(strategy, m, qualifier, inverter, ignore_multi_window, aspect_ratio, k)
        out = value * factor
        if kind == KIND_SP:
            out *= m.font_scale
        return out * m.density if px else out

    # -- percent space (literal % of a side) ----------------------------------------------
    def space_w(self, percent):
        return percent * 0.01 * self.metrics.width

    def space_h(self, percent):
        return percent * 0.01 * self.metrics.height

    def space_sw(self, percent):
        return percent * 0.01 * self.metrics.smallest_width

    def space(self, percent, reference):
        return percent * 0.01 * reference

    # -- facilitators (Android sdpRotate / sdpMode / sdpQualifier / sdpScreen) -------------
    def rotate(self, value, landscape_value, token="sdp"):
        """``value`` in portrait, ``landscape_value`` in landscape, both through ``token``."""
        f = self.fn(token)
        return f(landscape_value if self.metrics.is_landscape else value)

    def mode(self, value, ui_mode, mode_value, token="sdp"):
        """``mode_value`` when the UI mode matches (TV, car, watch, fold…), else ``value``."""
        return self.fn(token)(mode_value if self.metrics.ui_mode == ui_mode else value)

    def qualifier(self, value, rules, token="sdp", axis=DpQualifier.SMALL_WIDTH):
        """``rules`` = ``[(min_dp, value), …]``; the largest matching ``min_dp`` wins."""
        m = self.metrics
        d = m.smallest_width if axis == DpQualifier.SMALL_WIDTH else (
            m.height if axis == DpQualifier.HEIGHT else m.width)
        chosen, best = value, -1.0
        for min_dp, v in rules:
            if d >= min_dp and min_dp > best:
                chosen, best = v, min_dp
        return self.fn(token)(chosen)

    def screen(self, value, ui_mode=None, min_dp=0.0, screen_value=None, token="sdp"):
        """Combined rule: ``screen_value`` when ui mode (if given) matches and sw ≥ ``min_dp``."""
        m = self.metrics
        ok = (ui_mode is None or m.ui_mode == ui_mode) and m.smallest_width >= min_dp
        return self.fn(token)(screen_value if (ok and screen_value is not None) else value)

    # -- conversions ------------------------------------------------------------------------
    def to_px(self, dp):
        return dp * self.metrics.density

    def to_dp(self, px):
        return px / self.metrics.density

    @property
    def is_reference(self):
        m = self.metrics
        return m.smallest_width == BASE_WIDTH_DP and m.orientation != Orientation.LANDSCAPE


_SPACE = {"spaceW": "space_w", "spaceH": "space_h", "spaceSw": "space_sw", "vw": "space_w", "vh": "space_h"}
