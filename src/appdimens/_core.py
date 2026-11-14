"""AppDimens core — constants, enums, immutable metrics snapshot and the factor kernel.

Port of AppDimens Dynamic 3.2 (Android) / webdimens 3.2.1. Every formula and constant is
identical to the rest of the family and is pinned by ``tests/golden.json`` (generated from
the web reference implementation).

Compatible with CPython 3.7+ (Blender 2.83 → 4.x), PyPy and MicroPython-like subsets that
provide ``math``. No third-party dependencies.
"""

import math

__all__ = [
    "VERSION", "BASE_WIDTH_DP", "BASE_HEIGHT_DP", "BASE_DIAGONAL_DP", "BASE_PERIMETER_DP",
    "REFERENCE_ASPECT_RATIO", "INV_BASE_RATIO", "ADJUSTMENT_SCALE", "SENSITIVITY_DEFAULT",
    "FLUID_MIN_WIDTH", "FLUID_MAX_WIDTH", "FLUID_MIN_FACTOR", "FLUID_MAX_FACTOR",
    "AUTO_TRANSITION_DP", "LOG_SENSITIVITY", "POWER_EXPONENT",
    "DpQualifier", "Inverter", "Orientation", "UiModeType", "UnitType", "Strategy",
    "STRATEGIES", "STRATEGY_PREFIX", "VARIANTS", "SLOT_COUNT",
    "DimenMetrics", "compute_factor", "effective_qualifier", "read_screen_dp",
    "logarithmic_scale_for", "variant_slot",
]

VERSION = "3.2.0"

# ── Canonical constants (DesignScaleConstants.kt) ────────────────────────────
BASE_WIDTH_DP = 300.0
BASE_HEIGHT_DP = 533.0
BASE_DIAGONAL_DP = 611.6305  # family value (kept for bit-parity)
BASE_PERIMETER_DP = 833.0
REFERENCE_ASPECT_RATIO = 1.78
INV_BASE_RATIO = 1.0 / 300.0
ADJUSTMENT_SCALE = 0.1 / 30.0
SENSITIVITY_DEFAULT = 0.08 / 30.0
FLUID_MIN_WIDTH = 320.0
FLUID_MAX_WIDTH = 768.0
FLUID_MIN_FACTOR = 0.8
FLUID_MAX_FACTOR = 1.2
AUTO_TRANSITION_DP = 480.0
LOG_SENSITIVITY = 0.4
POWER_EXPONENT = 0.75
DENSITY_DPI_BASE = 160.0


class DpQualifier(object):
    """Screen axis that drives scaling (``sdp`` → SMALL_WIDTH, ``hdp`` → HEIGHT, ``wdp`` → WIDTH)."""
    SMALL_WIDTH = 0
    HEIGHT = 1
    WIDTH = 2


class Inverter(object):
    """Orientation-dependent axis swap (``Ph`` / ``Lh`` / ``Pw`` / ``Lw`` name tokens)."""
    DEFAULT = 0
    PH_TO_LW = 1
    PW_TO_LH = 2
    LH_TO_PW = 3
    LW_TO_PH = 4
    SW_TO_LH = 5
    SW_TO_LW = 6
    SW_TO_PH = 7
    SW_TO_PW = 8


class Orientation(object):
    DEFAULT = 0
    PORTRAIT = 1
    LANDSCAPE = 2


class UiModeType(object):
    NORMAL = "NORMAL"
    TELEVISION = "TELEVISION"
    CAR = "CAR"
    WATCH = "WATCH"
    DESK = "DESK"
    APPLIANCE = "APPLIANCE"
    VR_HEADSET = "VR_HEADSET"
    UNDEFINED = "UNDEFINED"
    FOLD_OPEN = "FOLD_OPEN"
    FOLD_CLOSED = "FOLD_CLOSED"
    FLIP_OPEN = "FLIP_OPEN"
    FLIP_CLOSED = "FLIP_CLOSED"
    FOLD_HALF_OPENED = "FOLD_HALF_OPENED"
    FLIP_HALF_OPENED = "FLIP_HALF_OPENED"


class UnitType(object):
    INCH = "INCH"
    CM = "CM"
    MM = "MM"
    SP = "SP"
    DP = "DP"
    PX = "PX"


class Strategy(object):
    """Scaling strategies. Integer ids index the precomputed factor tables."""
    SCALED = 0
    AUTO = 1
    PERCENT = 2
    POWER = 3
    FLUID = 4
    INTERPOLATED = 5
    LOGARITHMIC = 6
    DIAGONAL = 7
    PERIMETER = 8
    FIT = 9
    FILL = 10
    DENSITY = 11


STRATEGIES = ("scaled", "auto", "percent", "power", "fluid", "interpolated",
              "logarithmic", "diagonal", "perimeter", "fit", "fill", "density")

#: Name prefix of each strategy in the token grammar (``''`` → ``sdp``, ``'pw'`` → ``pwsdp``).
STRATEGY_PREFIX = ("", "a", "p", "pw", "f", "i", "log", "dg", "pr", "ft", "fl", "d")

_LINEAR_AR = (True, False, True, False, False, False, False, False, False, False, False, False)
_AXIS_FREE = (False, False, False, False, False, False, False, True, True, True, True, True)

#: Precomputed variants: (axis letter, qualifier, inverter, name token).
VARIANTS = (
    ("s", DpQualifier.SMALL_WIDTH, Inverter.DEFAULT, ""),
    ("h", DpQualifier.HEIGHT, Inverter.DEFAULT, ""),
    ("w", DpQualifier.WIDTH, Inverter.DEFAULT, ""),
    ("s", DpQualifier.SMALL_WIDTH, Inverter.SW_TO_PH, "Ph"),
    ("s", DpQualifier.SMALL_WIDTH, Inverter.SW_TO_LH, "Lh"),
    ("s", DpQualifier.SMALL_WIDTH, Inverter.SW_TO_PW, "Pw"),
    ("s", DpQualifier.SMALL_WIDTH, Inverter.SW_TO_LW, "Lw"),
    ("h", DpQualifier.HEIGHT, Inverter.PH_TO_LW, "Lw"),
    ("h", DpQualifier.HEIGHT, Inverter.LH_TO_PW, "Pw"),
    ("w", DpQualifier.WIDTH, Inverter.PW_TO_LH, "Lh"),
    ("w", DpQualifier.WIDTH, Inverter.LW_TO_PH, "Ph"),
)
SLOT_COUNT = len(VARIANTS) * 4
_VARIANT_INDEX = dict(((q, i), n) for n, (_a, q, i, _t) in enumerate(VARIANTS))


def variant_slot(qualifier, inverter=Inverter.DEFAULT, ignore_multi_window=False, aspect_ratio=False):
    """Table slot for a qualifier/inverter pair, or ``-1`` when it is not precomputed."""
    v = _VARIANT_INDEX.get((qualifier, inverter))
    if v is None:
        return -1
    return v * 4 + (1 if aspect_ratio else 0) + (2 if ignore_multi_window else 0)


def _finite_positive(v, fallback):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return fallback
    return v if (v > 0.0 and math.isfinite(v)) else fallback


def _non_negative(v):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return 0.0
    return v if (v > 0.0 and math.isfinite(v)) else 0.0


def logarithmic_scale_for(dim):
    """Logarithmic curve: ``1 + 0.4·ln(d/300)`` above 300, mirrored below."""
    if dim > BASE_WIDTH_DP:
        return 1.0 + LOG_SENSITIVITY * math.log(dim * INV_BASE_RATIO)
    if dim > 0.0:
        return 1.0 - LOG_SENSITIVITY * math.log(BASE_WIDTH_DP / dim)
    return 1.0


class DimenMetrics(object):
    """Immutable snapshot of one window/screen with every derived factor precomputed.

    Units: ``width``/``height`` are logical units (dp / CSS px / Qt logical px / GTK
    application px). ``density`` is physical pixels per logical unit. ``font_scale`` is the
    user's text-size preference (1.0 = default). ``dpi`` is the physical pixel density used
    by the physical units (mm/cm/inch); defaults to ``160 × density``.
    """

    __slots__ = (
        "width", "height", "smallest_width", "density", "font_scale", "dpi", "orientation",
        "ui_mode", "multi_window", "is_landscape", "is_portrait", "min_dim", "max_dim",
        "scale", "log_normalized_ar", "default_ar_multiplier", "default_scaled_ar_multiplier",
        "power_scale", "interpolated_scale", "diagonal_scale", "perimeter_scale",
        "logarithmic_scale", "_tables",
    )

    def __init__(self, width=BASE_WIDTH_DP, height=BASE_HEIGHT_DP, density=1.0, font_scale=1.0,
                 smallest_width=None, orientation=None, ui_mode=UiModeType.NORMAL,
                 multi_window=False, dpi=None):
        w = _non_negative(width)
        h = _non_negative(height)
        s = object.__setattr__
        s(self, "width", w)
        s(self, "height", h)
        mn = min(w, h)
        mx = max(w, h)
        s(self, "min_dim", mn)
        s(self, "max_dim", mx)
        s(self, "smallest_width", _finite_positive(smallest_width, mn))
        s(self, "density", _finite_positive(density, 1.0))
        s(self, "font_scale", _finite_positive(font_scale, 1.0))
        s(self, "dpi", _finite_positive(dpi, DENSITY_DPI_BASE * self.density))
        if orientation is None:
            orientation = (Orientation.LANDSCAPE if w > h else
                           (Orientation.PORTRAIT if (w > 0 or h > 0) else Orientation.DEFAULT))
        s(self, "orientation", orientation)
        s(self, "ui_mode", ui_mode)
        s(self, "multi_window", bool(multi_window))
        s(self, "is_landscape", orientation == Orientation.LANDSCAPE)
        s(self, "is_portrait", orientation == Orientation.PORTRAIT)

        sw = self.smallest_width if self.smallest_width > 0 else BASE_WIDTH_DP
        s(self, "scale", sw * INV_BASE_RATIO)
        raw_ar = (mx / mn) if mn > 0 else 1.0
        n_ar = raw_ar / REFERENCE_ASPECT_RATIO
        if not (n_ar > 0 and math.isfinite(n_ar)):
            n_ar = 1.0
        log_ar = math.log(n_ar)
        s(self, "log_normalized_ar", log_ar)
        s(self, "default_ar_multiplier", 1.0 + SENSITIVITY_DEFAULT * log_ar)
        s(self, "default_scaled_ar_multiplier",
          1.0 + (sw - BASE_WIDTH_DP) * (ADJUSTMENT_SCALE + SENSITIVITY_DEFAULT * log_ar))
        s(self, "power_scale", math.pow(sw / BASE_WIDTH_DP, POWER_EXPONENT))
        s(self, "interpolated_scale", 1.0 + (sw * INV_BASE_RATIO - 1.0) * 0.5)
        s(self, "diagonal_scale", math.sqrt(mn * mn + mx * mx) / BASE_DIAGONAL_DP)
        s(self, "perimeter_scale", (mn + mx) / BASE_PERIMETER_DP)
        s(self, "logarithmic_scale", logarithmic_scale_for(sw))
        s(self, "_tables", [None] * len(STRATEGIES))

    def __setattr__(self, name, value):
        raise AttributeError("DimenMetrics is immutable; build a new snapshot")

    def __repr__(self):
        return ("DimenMetrics(width=%g, height=%g, density=%g, font_scale=%g, multi_window=%s)"
                % (self.width, self.height, self.density, self.font_scale, self.multi_window))

    def __eq__(self, other):
        return isinstance(other, DimenMetrics) and self._key() == other._key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._key())

    def _key(self):
        return (self.width, self.height, self.smallest_width, self.density, self.font_scale,
                self.dpi, self.orientation, self.ui_mode, self.multi_window)

    def replace(self, **changes):
        """Copy with some inputs changed (``m.replace(width=1024)``)."""
        kw = dict(width=self.width, height=self.height, density=self.density,
                  font_scale=self.font_scale, smallest_width=None, orientation=None,
                  ui_mode=self.ui_mode, multi_window=self.multi_window, dpi=None)
        kw.update(changes)
        return DimenMetrics(**kw)

    # -- factor tables -------------------------------------------------------------------
    def table(self, strategy):
        """The 44 precomputed factors of ``strategy`` (built lazily, then O(1))."""
        t = self._tables[strategy]
        if t is None:
            t = _build_table(strategy, self)
            self._tables[strategy] = t
        return t

    def scaled_multiplier(self, aspect_ratio, k=None):
        if not aspect_ratio:
            return self.scale
        if k is None:
            return self.default_scaled_ar_multiplier
        _assert_k(k)
        return 1.0 + (self.smallest_width - BASE_WIDTH_DP) * (ADJUSTMENT_SCALE + k * self.log_normalized_ar)

    def ar_multiplier(self, k=None):
        if k is None:
            return self.default_ar_multiplier
        _assert_k(k)
        return 1.0 + k * self.log_normalized_ar


def _assert_k(k):
    if not math.isfinite(k):
        raise ValueError("custom sensitivity k must be finite")


def effective_qualifier(qualifier, inverter, is_landscape, is_portrait):
    """Port of ``DimenCalculationPlumbing.effectiveQualifier``."""
    Q, I = DpQualifier, Inverter
    if inverter == I.DEFAULT:
        return qualifier
    if inverter == I.PH_TO_LW:
        return Q.WIDTH if (is_landscape and qualifier == Q.HEIGHT) else qualifier
    if inverter == I.PW_TO_LH:
        return Q.HEIGHT if (is_landscape and qualifier == Q.WIDTH) else qualifier
    if inverter == I.LH_TO_PW:
        return Q.WIDTH if (is_portrait and qualifier == Q.HEIGHT) else qualifier
    if inverter == I.LW_TO_PH:
        return Q.HEIGHT if (is_portrait and qualifier == Q.WIDTH) else qualifier
    if inverter == I.SW_TO_LH:
        return Q.HEIGHT if (is_landscape and qualifier == Q.SMALL_WIDTH) else qualifier
    if inverter == I.SW_TO_LW:
        return Q.WIDTH if (is_landscape and qualifier == Q.SMALL_WIDTH) else qualifier
    if inverter == I.SW_TO_PH:
        return Q.HEIGHT if (is_portrait and qualifier == Q.SMALL_WIDTH) else qualifier
    if inverter == I.SW_TO_PW:
        return Q.WIDTH if (is_portrait and qualifier == Q.SMALL_WIDTH) else qualifier
    return qualifier


def read_screen_dp(m, q):
    if q == DpQualifier.HEIGHT:
        return m.height
    if q == DpQualifier.WIDTH:
        return m.width
    return m.smallest_width


def _base_scale(strategy, m, q, is_default_sw):
    S = Strategy
    if strategy == S.SCALED or strategy == S.PERCENT:
        return m.scale if is_default_sw else read_screen_dp(m, q) * INV_BASE_RATIO
    if strategy == S.AUTO:
        d = read_screen_dp(m, q)
        if d <= AUTO_TRANSITION_DP:
            return d * INV_BASE_RATIO
        return (AUTO_TRANSITION_DP * INV_BASE_RATIO
                + LOG_SENSITIVITY * math.log(1.0 + (d - AUTO_TRANSITION_DP) * INV_BASE_RATIO))
    if strategy == S.POWER:
        return m.power_scale if is_default_sw else math.pow(read_screen_dp(m, q) / BASE_WIDTH_DP, POWER_EXPONENT)
    if strategy == S.FLUID:
        d = read_screen_dp(m, q)
        if d <= FLUID_MIN_WIDTH:
            return FLUID_MIN_FACTOR
        if d >= FLUID_MAX_WIDTH:
            return FLUID_MAX_FACTOR
        return FLUID_MIN_FACTOR + ((FLUID_MAX_FACTOR - FLUID_MIN_FACTOR) * (d - FLUID_MIN_WIDTH)
                                   / (FLUID_MAX_WIDTH - FLUID_MIN_WIDTH))
    if strategy == S.INTERPOLATED:
        return m.interpolated_scale if is_default_sw else 1.0 + (read_screen_dp(m, q) * INV_BASE_RATIO - 1.0) * 0.5
    if strategy == S.LOGARITHMIC:
        return m.logarithmic_scale if is_default_sw else logarithmic_scale_for(read_screen_dp(m, q))
    if strategy == S.DIAGONAL:
        return m.diagonal_scale
    if strategy == S.PERIMETER:
        return m.perimeter_scale
    if strategy == S.FIT:
        return min(m.min_dim / BASE_WIDTH_DP, m.max_dim / BASE_HEIGHT_DP)
    if strategy == S.FILL:
        return max(m.min_dim / BASE_WIDTH_DP, m.max_dim / BASE_HEIGHT_DP)
    if strategy == S.DENSITY:
        return m.density
    raise ValueError("unknown strategy %r" % (strategy,))


def compute_factor(strategy, m, qualifier=DpQualifier.SMALL_WIDTH, inverter=Inverter.DEFAULT,
                   ignore_multi_window=False, aspect_ratio=False, k=None):
    """Fully general factor (any inverter, custom sensitivity ``k``). The hot path reads the
    precomputed tables built with this same function."""
    if ignore_multi_window and m.multi_window:
        return 1.0
    q = qualifier if _AXIS_FREE[strategy] else effective_qualifier(
        qualifier, inverter, m.is_landscape, m.is_portrait)
    if _LINEAR_AR[strategy]:
        if qualifier == DpQualifier.SMALL_WIDTH and inverter == Inverter.DEFAULT:
            return m.scaled_multiplier(aspect_ratio, k)
        dim = read_screen_dp(m, q)
        if not aspect_ratio:
            return dim * INV_BASE_RATIO
        if k is None:
            k = SENSITIVITY_DEFAULT
        else:
            _assert_k(k)
        return 1.0 + (dim - BASE_WIDTH_DP) * (ADJUSTMENT_SCALE + k * m.log_normalized_ar)
    base = _base_scale(strategy, m, q,
                       qualifier == DpQualifier.SMALL_WIDTH and inverter == Inverter.DEFAULT)
    return base * m.ar_multiplier(k) if aspect_ratio else base


def _build_table(strategy, m):
    out = []
    mw = m.multi_window
    for (_a, q, inv, _t) in VARIANTS:
        plain = compute_factor(strategy, m, q, inv, False, False)
        ar = compute_factor(strategy, m, q, inv, False, True)
        out.extend((plain, ar, 1.0 if mw else plain, 1.0 if mw else ar))
    return tuple(out)
