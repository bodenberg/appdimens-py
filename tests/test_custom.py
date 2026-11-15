"""Custom strategies: the cross-platform fixture (540 cases from the Kotlin reference) + API behaviour."""
import json
import math
import os

import pytest

import appdimens as ad
from appdimens import custom as c

FIXTURE = json.load(open(os.path.join(os.path.dirname(__file__), "custom-strategy-fixture.json")))


@pytest.fixture(autouse=True)
def _clean():
    c.reset_for_test()
    yield
    c.reset_for_test()


def _screen(s):
    return c.ScreenSnapshot(s["width"], s["height"], s["smallestWidth"], s["density"], s["fontScale"],
                            s["landscape"], s["multiWindow"], s["device"])


def test_cross_platform_fixture():
    tol = FIXTURE["tolerance"]
    strategies, default_id = c.decode_strategies(FIXTURE["document"])
    screens = {k: _screen(v) for k, v in FIXTURE["screens"].items()}
    assert len(FIXTURE["cases"]) == 540
    bad = []
    for case in FIXTURE["cases"]:
        r = strategies[case["strategy"]].resolve(screens[case["screen"]])
        base = case["base"]
        for key, got in (("factor", r.factor), ("dp", r.scale(base)), ("spDp", r.scale_sp_dp(base))):
            want = case[key]
            if abs(want - got) > tol * max(1.0, abs(want)):
                bad.append((case["strategy"], case["screen"], base, key, want, got))
        if list(r.applied_rules) != case["rules"]:
            bad.append((case["strategy"], case["screen"], "rules", case["rules"], list(r.applied_rules)))
    assert not bad, bad[:10]
    assert default_id == "brand"


def test_round_trip_json():
    strategies, _ = c.decode_strategies(FIXTURE["document"])
    text = c.export_scaling_strategies(strategies.values(), "brand")
    again, d = c.decode_strategies(text)
    screens = [_screen(v) for v in FIXTURE["screens"].values()]
    for sid, s in strategies.items():
        for scr in screens:
            assert again[sid].resolve(scr).scale(16) == pytest.approx(s.resolve(scr).scale(16), rel=1e-12)
    assert d == "brand"


def test_code_and_text_formulas():
    scr = c.ScreenSnapshot(720, 1280, density=2)
    product = c.custom_scale_strategy(lambda s: s.clamp(s.width / 360, 0.85, 1.8))
    assert product.dp(10, scr) == pytest.approx(18.0)
    text = c.scaling_formula("base * pow(sw / 360, 0.8)")
    assert text.dp(10, scr) == pytest.approx(10 * (720 / 360) ** 0.8)
    assert c.scaling_formula("base * pow(sw / 360, 0.8)") is text          # shared per text
    code = c.scaling_formula(lambda f: f.base * f.pow(f.sw / 360, 0.8))
    assert code.dp(10, scr) == pytest.approx(text.dp(10, scr))
    tern = c.scaling_formula("tablet ? base * 1.5 : base")
    assert tern.dp(10, scr) == 15 and tern.dp(10, c.ScreenSnapshot(360, 640)) == 10
    assert text.px(10, scr) == pytest.approx(2 * text.dp(10, scr))


def test_registry_default_and_short_functions():
    ad.set_metrics(ad.DimenMetrics(width=600, height=1024, density=2, font_scale=1.5))
    c.load_scaling_strategies(FIXTURE["document"])
    assert c.get_default_scaling_strategy().id == "brand"
    assert c.cdp(16) == pytest.approx(c.require_scaling_strategy("brand").dp(16))
    assert c.csp(14, "brand") == pytest.approx(c.cdp(14, "brand") * 1.3)   # fontScale clamp 1.3
    assert c.cdp_px(16, "scaled") == pytest.approx(16 * 2 * 2)
    assert c.cdp(16, "base * 2") == 32                                        # text formula
    assert c.get_scaling_strategy("gamehud") is c.CustomPresets.GAME_HUD
    with pytest.raises(ValueError):
        c.require_scaling_strategy("nope")


def test_parity_with_core_builtins():
    for w, h in ((360, 800), (800, 1280), (1920, 1080)):
        m = ad.DimenMetrics(width=w, height=h)
        d = ad.Dimens(m)
        assert c.BuiltInStrategies.SCALED.dp(10, m) == pytest.approx(d.sdp(10), rel=1e-12)
        assert c.BuiltInStrategies.POWER.dp(10, m) == pytest.approx(d.pwsdp(10), rel=1e-12)
        assert c.BuiltInStrategies.LOGARITHMIC.dp(10, m) == pytest.approx(d.logsdp(10), rel=1e-12)
        assert c.BuiltInStrategies.INTERPOLATED.dp(10, m) == pytest.approx(d.isdp(10), rel=1e-12)
        assert c.BuiltInStrategies.FIXED.dp(10, m) == 10


def test_errors_carry_paths():
    with pytest.raises(ValueError, match=r"brand.curve.type 'cubic'"):
        c.decode_strategies({"strategies": [{"id": "brand", "curve": {"type": "cubic"}}]})
    with pytest.raises(ValueError, match=r"x.formula: Invalid expression at 7: unknown variable 'swx'"):
        c.decode_strategies({"strategies": [{"id": "x", "formula": "base * swx"}]})
    with pytest.raises(ValueError, match="Cyclic"):
        c.decode_strategies({"strategies": [{"id": "a", "extends": "b"}, {"id": "b", "extends": "a"}]})
    with pytest.raises(ValueError, match="'pow' takes 2"):
        c.ScalingExpression.parse("pow(1)")
    with pytest.raises(ValueError, match="cannot be encoded"):
        c.custom_scale_strategy(lambda s: 1).to_json()


def test_value_clamp_and_multi_window():
    s = c.define_scaling_strategy({"id": "t", "valueClamp": {"min": 10, "max": 32}, "ignoreMultiWindow": True})
    big = c.ScreenSnapshot(1200, 1600)
    assert s.dp(100, big) == 32 and s.dp(-100, big) == -32 and s.dp(1, big) == 10 and s.dp(0, big) == 0
    mw = c.ScreenSnapshot(1200, 1600, multi_window=True)
    assert s.factor(mw) == 1


def test_explain_and_axis_variant():
    s = c.require_scaling_strategy("tvSafe")
    tv = c.ScreenSnapshot(960, 540, device="tv")
    assert "rules=['tv']" in s.explain(tv)
    assert s.with_axis("width").id == "tvSafe@width" and s.with_axis("width") is s.with_axis("width")
