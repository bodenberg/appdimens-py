"""Physical units (Android ``appdimens-dynamic-units``): mm / cm / inch ↔ dp / px / sp.

Conversions use the snapshot's ``dpi`` (physical pixels per inch) and ``density``
(physical pixels per logical unit): ``dp = inches × dpi / density``. Pass real panel DPI
(e.g. from Qt ``physicalDotsPerInch``, GDK monitor mm size, EDID) for true physical size.
"""

import math

from ._core import UnitType

__all__ = ["mm", "cm", "inch", "mm_px", "cm_px", "inch_px", "mm_sp", "cm_sp", "inch_sp",
           "convert_mm_to_cm", "convert_mm_to_inch", "convert_cm_to_mm", "convert_cm_to_inch",
           "convert_inch_to_cm", "convert_inch_to_mm", "unit_size_in_dp", "radius",
           "radius_from_circumference", "measure_diameter", "MM_PER_INCH"]

MM_PER_INCH = 25.4


def _m(metrics):
    if metrics is None:
        from . import default_scope
        return default_scope().metrics
    return metrics


def inch(value, metrics=None):
    """Inches → dp (logical units)."""
    m = _m(metrics)
    return value * m.dpi / m.density


def mm(value, metrics=None):
    """Millimetres → dp."""
    return inch(value / MM_PER_INCH, metrics)


def cm(value, metrics=None):
    """Centimetres → dp."""
    return inch(value * 10.0 / MM_PER_INCH, metrics)


def inch_px(value, metrics=None):
    return value * _m(metrics).dpi


def mm_px(value, metrics=None):
    return value / MM_PER_INCH * _m(metrics).dpi


def cm_px(value, metrics=None):
    return value * 10.0 / MM_PER_INCH * _m(metrics).dpi


def inch_sp(value, metrics=None):
    """Text size (sp) that renders at that physical size under the current font scale."""
    m = _m(metrics)
    return inch(value, m) / m.font_scale


def mm_sp(value, metrics=None):
    m = _m(metrics)
    return mm(value, m) / m.font_scale


def cm_sp(value, metrics=None):
    m = _m(metrics)
    return cm(value, m) / m.font_scale


convert_mm_to_cm = lambda v: v / 10.0  # noqa: E731
convert_mm_to_inch = lambda v: v / MM_PER_INCH  # noqa: E731
convert_cm_to_mm = lambda v: v * 10.0  # noqa: E731
convert_cm_to_inch = lambda v: v * 10.0 / MM_PER_INCH  # noqa: E731
convert_inch_to_cm = lambda v: v * MM_PER_INCH / 10.0  # noqa: E731
convert_inch_to_mm = lambda v: v * MM_PER_INCH  # noqa: E731


def unit_size_in_dp(unit, metrics=None):
    m = _m(metrics)
    if unit == UnitType.INCH:
        return inch(1.0, m)
    if unit == UnitType.CM:
        return cm(1.0, m)
    if unit == UnitType.MM:
        return mm(1.0, m)
    if unit == UnitType.SP:
        return m.font_scale
    if unit == UnitType.PX:
        return 1.0 / m.density
    return 1.0


def radius(diameter, unit=UnitType.DP, metrics=None):
    return diameter * unit_size_in_dp(unit, metrics) / 2.0


def radius_from_circumference(circumference, unit=UnitType.DP, metrics=None):
    return circumference * unit_size_in_dp(unit, metrics) / (2.0 * math.pi)


def measure_diameter(value, is_circumference):
    return value / math.pi if is_circumference else value
