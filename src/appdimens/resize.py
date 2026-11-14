"""Constraint-based resize (Android ``ResizeMath`` / ``AutoResizeText``).

Picks the **largest** step in ``[min, max]`` that still satisfies a monotone ``fits``
predicate, with a binary search over a pre-built step table — O(log n) measurements.
"""

__all__ = ["MAX_RESIZE_STEPS", "build_steps", "find_largest_fitting", "ResizeRange", "auto_resize_text"]

MAX_RESIZE_STEPS = 4096


def build_steps(lo, hi, step):
    """Ascending candidates ``lo, lo+step, …, hi`` (always contains ``hi``; no float drift)."""
    lo, hi = float(min(lo, hi)), float(max(lo, hi))
    if not (step > 0):
        return (lo,)
    eps = step * 1e-4
    out = []
    n = 0
    x = lo
    while x <= hi + eps and n < MAX_RESIZE_STEPS:
        out.append(min(x, hi))
        n += 1
        x = lo + n * step
    if out[-1] < hi - eps and n < MAX_RESIZE_STEPS:
        out.append(hi)
    return tuple(out)


def find_largest_fitting(steps, fits):
    """Largest candidate where ``fits(candidate)`` is true; ``0`` when none fits."""
    n = len(steps)
    if n == 0:
        return 0.0
    left, right, best = 0, n - 1, 0.0
    while left <= right:
        mid = (left + right) >> 1
        v = steps[mid]
        if fits(v):
            best = v
            left = mid + 1
        else:
            right = mid - 1
    return best


class ResizeRange(object):
    """A resolved ``[min, max]`` range with its cached step table."""
    __slots__ = ("min", "max", "step", "steps")

    def __init__(self, min_value, max_value, step=1.0):
        self.min, self.max, self.step = float(min_value), float(max_value), float(step)
        self.steps = build_steps(self.min, self.max, self.step)

    def fit(self, fits):
        best = find_largest_fitting(self.steps, fits)
        return best if best > 0 else self.steps[0]


def auto_resize_text(text, max_width, max_height, measure, min_size=8.0, max_size=96.0, step=0.5):
    """Largest font size whose ``measure(text, size) -> (w, h)`` fits the box.

    ``measure`` can wrap Pillow ``ImageFont``, Qt ``QFontMetricsF``, Blender ``blf.dimensions``,
    pygame ``font.size`` … Returns ``min_size`` when nothing fits.
    """
    def fits(size):
        w, h = measure(text, size)
        return w <= max_width and h <= max_height
    return ResizeRange(min_size, max_size, step).fit(fits)
