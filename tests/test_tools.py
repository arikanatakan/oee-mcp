import json

import pytest

from oee_mcp import _tools as t
from oee_mcp._tools import DowntimeEvent, MachineInput, ProductionRun, YieldStep


def _vorne():
    return MachineInput(planned_production_time=420, downtime=47, ideal_rate=60,
                        total_count=19271, reject_count=423, all_time=480)


def test_compute_oee():
    r = t.compute_oee(_vorne())
    assert r["factors"]["oee"] == pytest.approx(0.748, abs=0.001)
    assert r["factors"]["teep"] == pytest.approx(0.654, abs=0.001)
    assert "summary" in r and "OEE" in r["summary"]


def test_compute_oee_error_has_hint():
    r = t.compute_oee(MachineInput(planned_production_time=420, downtime=47,
                                   ideal_rate=60, total_count=100))
    assert "error" in r
    assert "describe_inputs" in r["hint"]


def test_oee_from_log():
    r = t.oee_from_log(
        420, runs=[ProductionRun(count=19271, good=18848, ideal_rate=60)],
        downtime_events=[DowntimeEvent(reason="jam", duration=47)])
    assert r["factors"]["oee"] == pytest.approx(0.748, abs=0.001)
    assert r["downtime_reasons"] == {"jam": 47}


def test_oee_from_factors():
    r = t.oee_from_factors(0.90, 0.95, 0.999)
    assert r["factors"]["oee"] == pytest.approx(0.854, abs=0.001)


def test_aggregate_is_not_the_average():
    m1 = MachineInput(planned_production_time=100, run_time=90, ideal_cycle_time=1,
                      total_count=80, good_count=80, name="M1")
    m2 = MachineInput(planned_production_time=300, run_time=150, ideal_cycle_time=1,
                      total_count=150, good_count=135, name="M2")
    r = t.aggregate_oee([m1, m2])
    assert r["factors"]["oee"] == pytest.approx(0.5375, abs=1e-3)
    assert len(r["machines"]) == 2


def test_describe_inputs():
    d = t.describe_inputs()
    assert "planned_production_time" in d["machine_fields"]
    assert d["definitions"]
    assert d["six_big_losses"]


def test_payload_is_json_serializable():
    json.dumps(t.compute_oee(_vorne()))


def test_compute_oee_reports_ooe():
    r = t.compute_oee(MachineInput(
        planned_production_time=420, downtime=47, ideal_rate=60,
        total_count=19271, reject_count=423, all_time=480, planned_downtime=33))
    f = r["factors"]
    assert f["ooe"] is not None
    assert f["teep"] <= f["ooe"] <= f["oee"]


def test_reliability_tool():
    r = t.reliability(1000, failures=5, total_repair_time=50)
    assert r["mtbf"] == pytest.approx(200)
    assert r["availability"] == pytest.approx(1000 / 1050)


def test_rolled_throughput_yield_tool():
    r = t.rolled_throughput_yield([YieldStep(value=0.99), YieldStep(value=0.98)])
    assert r["rty"] == pytest.approx(0.99 * 0.98)
    r2 = t.rolled_throughput_yield([YieldStep(good=95, total=100)])
    assert r2["step_yields"][0] == pytest.approx(0.95)


def test_capacity_tool():
    r = t.capacity(480, 240, cycle_time=1.5)
    assert r["takt_time"] == pytest.approx(2.0)
    assert r["meets_demand"] is True


def test_loss_value_tool():
    r = t.loss_value(MachineInput(
        planned_production_time=480, downtime=80, ideal_cycle_time=0.5,
        total_count=700, reject_count=100), value_per_unit=10)
    assert r["lost_units"]["total"] == pytest.approx(360)
    assert r["lost_value"]["total"] == pytest.approx(3600)


def test_charts_return_png_bytes():
    m = MachineInput(planned_production_time=480, downtime=80, ideal_cycle_time=0.5,
                     total_count=700, reject_count=100, setup_time=30,
                     startup_rejects=40)
    for png in (t.waterfall_png(m), t.loss_pareto_png(m), t.trend_png([m, m])):
        assert isinstance(png, bytes)
        assert png[:4] == b"\x89PNG"
