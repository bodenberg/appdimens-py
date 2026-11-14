import math
import threading

import pytest

import appdimens as ad
from appdimens import DimenMetrics, Dimens, parse_token, units, resize


def test_reference_identity():
    d = Dimens()
    for name in ("sdp", "asdp", "pwsdp", "isdp", "logsdp", "ftsdp", "flsdp", "dgsdp", "prsdp", "psdp"):
        assert getattr(d, name)(16) == pytest.approx(16, rel=1e-3), name


def test_auto_curve():
    d = Dimens(DimenMetrics(width=480, height=800))
    assert d.asdp(10) == pytest.approx(16.0)
    d.update(width=780, height=1280)
    assert d.asdp(10) == pytest.approx(10 * (1.6 + 0.4 * math.log(2.0)))


def test_parser_grammar():
    assert parse_token("sdp") == (0, 0, 0, 0, False, False, False)
    assert parse_token("asdpia")[5:] == (True, True)
    assert parse_token("sdpPxaPh") == parse_token("sdpPhaPx")
    assert parse_token("logwsp")[0] == 6 and parse_token("logwsp")[3] == 1
    for bad in ("sdpp", "xdp", "hdpPh", "sdpaa", "", "sdpPxPx", "sdpaPhi"):
        with pytest.raises(ValueError):
            parse_token(bad)


def test_module_tokens_and_strings():
    ad.set_metrics(DimenMetrics(width=360, height=800, density=3, font_scale=1.2))
    assert ad.sdp(10) == pytest.approx(12.0)
    assert ad.ssp(10) == pytest.approx(14.4)
    assert ad.sem(10) == pytest.approx(12.0)
    assert ad.sdpPx(10) == pytest.approx(36.0)
    assert ad.hdpLw(1) > 0
    assert ad.dimen("10sdp") == pytest.approx(12.0)
    assert ad.dimen("50spaceW") == pytest.approx(180.0)
    assert ad.dimen("3px") == pytest.approx(1.0)
    with pytest.raises(AttributeError):
        ad.notatoken


def test_multi_window_bypass():
    d = Dimens(DimenMetrics(width=1024, height=600, multi_window=True))
    assert d.sdpi(16) == 16
    assert d.sdp(16) != 16


def test_listeners_and_noop_update():
    d = Dimens()
    seen = []
    remove = d.add_listener(seen.append)
    assert d.update(width=400) is True
    assert d.update(width=400) is False
    remove()
    d.update(width=500)
    assert len(seen) == 1


def test_metrics_immutable_and_sanitised():
    m = DimenMetrics(width=float("nan"), height=-5, density=0, font_scale=None)
    assert m.width == 0 and m.density == 1 and m.font_scale == 1
    with pytest.raises(AttributeError):
        m.width = 3
    assert Dimens(m).sdp(10) == pytest.approx(10.0)  # falls back to the reference


def test_custom_k_and_resolve():
    d = Dimens(DimenMetrics(width=600, height=1600))
    assert d.resolve(10, aspect_ratio=True, k=0.0) == pytest.approx(10 * (1 + 300 * 0.1 / 30))
    with pytest.raises(ValueError):
        d.resolve(10, aspect_ratio=True, k=float("inf"))


def test_facilitators():
    d = Dimens(DimenMetrics(width=800, height=400, ui_mode="TELEVISION"))
    assert d.rotate(10, 20) == d.sdp(20)
    assert d.mode(10, "TELEVISION", 30) == d.sdp(30)
    assert d.qualifier(10, [(300, 12), (600, 20)]) == d.sdp(12)
    assert d.screen(10, "TELEVISION", 300, 40) == d.sdp(40)


def test_units():
    m = DimenMetrics(density=2.0, dpi=320)
    assert units.inch(1, m) == pytest.approx(160.0)
    assert units.mm(25.4, m) == pytest.approx(160.0)
    assert units.cm_px(2.54, m) == pytest.approx(320.0)
    assert units.convert_inch_to_mm(1) == 25.4


def test_resize():
    steps = resize.build_steps(8, 12, 1.5)
    assert steps == (8.0, 9.5, 11.0, 12.0)
    assert resize.find_largest_fitting(steps, lambda s: s < 11.5) == 11.0
    size = resize.auto_resize_text("hello", 100, 30, lambda t, s: (len(t) * s * 0.6, s * 1.2), 6, 72, 0.5)
    assert size == pytest.approx(25.0)  # height-bound: 1.2·s ≤ 30


def test_thread_safety_smoke():
    d = Dimens()
    errors = []

    def writer():
        for i in range(2000):
            d.update(width=300 + i % 700, height=900)

    def reader():
        try:
            for _ in range(20000):
                v = d.sdp(10)
                assert 9.99 < v < 34
        except Exception as e:  # pragma: no cover
            errors.append(e)
    ts = [threading.Thread(target=writer)] + [threading.Thread(target=reader) for _ in range(3)]
    [t.start() for t in ts]
    [t.join() for t in ts]
    assert not errors
