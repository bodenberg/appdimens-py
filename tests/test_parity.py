"""Parity with appdimens-dynamic (tests/golden.json generated from its verbatim kernels, float32)."""
import json
import math
import os

import pytest

import appdimens as ad
from appdimens import DimenMetrics, Dimens, compute_factor, VARIANTS, STRATEGIES

GOLDEN = json.load(open(os.path.join(os.path.dirname(__file__), "golden.json")))
INV = {"DEFAULT": 0, "PH_TO_LW": 1, "PW_TO_LH": 2, "LH_TO_PW": 3, "LW_TO_PH": 4,
       "SW_TO_LH": 5, "SW_TO_LW": 6, "SW_TO_PH": 7, "SW_TO_PW": 8}
Q = {"SMALL_WIDTH": 0, "HEIGHT": 1, "WIDTH": 2}


def _metrics(c):
    return DimenMetrics(width=c["w"], height=c["h"], density=c["density"],
                        font_scale=c["fontScale"], multi_window=c["multiWindow"])


def test_layout_matches():
    assert GOLDEN["strategies"] == list(STRATEGIES)
    for v, g in zip(VARIANTS, GOLDEN["variants"]):
        assert v[0] == g["axis"] and v[1] == Q[g["qualifier"]] and v[2] == INV[g["inverter"]] and v[3] == g["token"]


@pytest.mark.parametrize("case", GOLDEN["cases"], ids=lambda c: "%gx%g" % (c["w"], c["h"]))
def test_factor_tables(case):
    m = _metrics(case)
    for sid, name in enumerate(STRATEGIES):
        assert list(m.table(sid)) == pytest.approx(case["factors"][name], rel=2e-6, abs=1e-6), name
    assert compute_factor(0, m, 0, 0, False, True, 0.01) == pytest.approx(case["customK001"]["scaled"], rel=2e-6)
    assert compute_factor(1, m, 0, 0, False, True, 0.01) == pytest.approx(case["customK001"]["auto"], rel=2e-6)


@pytest.mark.parametrize("case", GOLDEN["cases"][:6], ids=lambda c: "%gx%g" % (c["w"], c["h"]))
def test_token_resolvers(case):
    d = Dimens(_metrics(case))
    f = case["factors"]
    assert d.sdp(10) == pytest.approx(10 * f["scaled"][0])
    assert d.asdpa(10) == pytest.approx(10 * f["auto"][1])
    assert d.hdpi(10) == pytest.approx(10 * f["scaled"][4 + 2])
    assert d.wspia(10) == pytest.approx(10 * f["scaled"][8 + 3] * case["fontScale"])
    assert d.sem(10) == pytest.approx(10 * f["scaled"][0])
    assert d.sdpPx(10) == pytest.approx(10 * f["scaled"][0] * case["density"])
    assert d.sdpPh(10) == pytest.approx(10 * f["scaled"][12])
    assert d.sdpPxiaPh(10) == pytest.approx(10 * f["scaled"][15] * case["density"])
    assert d.hdpLwa(10) == pytest.approx(10 * f["scaled"][29])
    assert d.logssp(10) == pytest.approx(10 * f["logarithmic"][0] * case["fontScale"])
    assert d.ftsdp(10) == pytest.approx(10 * f["fit"][0])
    assert d.dgwdp(10) == pytest.approx(10 * f["diagonal"][8])
