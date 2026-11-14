"""Micro-benchmark: ns per resolver call (hot path) vs. full general path."""
import os
import sys
import timeit

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
import appdimens as ad  # noqa: E402

ad.set_metrics(ad.DimenMetrics(width=411, height=914, density=2.625))
N = 1_000_000
for label, stmt in (("sdp(16)", "ad.sdp(16)"), ("asdpa(16)", "ad.asdpa(16)"), ("sspPx(14)", "ad.sspPx(14)"),
                    ("sdpPh(16)", "ad.sdpPh(16)"), ("resolve(custom k)", "ad.resolve(16, aspect_ratio=True, k=0.01)"),
                    ('dimen("16asdp")', 'ad.dimen("16asdp")')):
    t = min(timeit.repeat(stmt, globals={"ad": ad}, number=N, repeat=3))
    print("%-20s %7.1f ns/call" % (label, t / N * 1e9))
t = min(timeit.repeat("ad.DimenMetrics(width=1280, height=800)", globals={"ad": ad}, number=20000, repeat=3))
print("%-20s %7.2f µs" % ("new snapshot", t / 20000 * 1e6))
