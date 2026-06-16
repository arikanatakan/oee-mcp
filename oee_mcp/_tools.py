"""Tool logic, kept free of the MCP SDK so it can be tested directly.

Each analysis tool calls the oee library and returns its JSON-safe payload
(factors, time waterfall, six big losses, provenance) plus a plain-language
summary. Chart helpers render a PNG.
"""

from __future__ import annotations

import io

import matplotlib

matplotlib.use("Agg")

import oee  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

SIGN_AND_UNITS = (
    "All times must be in the same unit; ideal_cycle_time is that unit per piece "
    "(or pass ideal_rate in pieces per that unit). Performance above 100% is "
    "capped and flagged."
)

DEFINITIONS = [
    "Availability = run time / planned production time",
    "Performance = (ideal cycle time x total count) / run time",
    "Quality = good count / total count",
    "OEE = Availability x Performance x Quality",
    "TEEP = OEE x utilization, with utilization = planned production time / all time",
    "World-class OEE >= 85% (availability >= 90%, performance >= 95%, "
    "quality >= 99.9%) [Nakajima, 1988]",
]

SIX_BIG_LOSSES = [
    "Availability: breakdowns, setup and adjustments",
    "Performance: minor stops, reduced speed (reported combined)",
    "Quality: process defects, reduced yield (startup rejects)",
]


class MachineInput(BaseModel):
    """One machine or shift, by times and piece counts."""

    planned_production_time: float = Field(
        description="Scheduled production time (any unit, used consistently).")
    total_count: float = Field(description="Total pieces produced (good and bad).")
    run_time: float | None = Field(
        default=None, description="Actual run time; give this or downtime.")
    downtime: float | None = Field(default=None, description="Stop time within planned time.")
    ideal_cycle_time: float | None = Field(
        default=None, description="Time per piece at max speed; give this or ideal_rate.")
    ideal_rate: float | None = Field(default=None, description="Pieces per time unit at max speed.")
    good_count: float | None = Field(
        default=None, description="Good pieces; give this or reject_count.")
    reject_count: float | None = Field(default=None, description="Rejected pieces.")
    all_time: float | None = Field(
        default=None, description="Total calendar time, for TEEP and utilization.")
    setup_time: float | None = Field(
        default=None,
        description="Planned-stop time within downtime; splits availability into "
        "setup-and-adjustments and breakdowns.")
    startup_rejects: float | None = Field(
        default=None,
        description="Rejects at startup; splits quality into reduced yield and "
        "process defects.")
    name: str | None = Field(default=None, description="Optional label.")


class ProductionRun(BaseModel):
    """One production run in an event log."""

    count: float = Field(description="Pieces produced in this run.")
    good: float | None = Field(default=None, description="Good pieces; give this or reject.")
    reject: float | None = Field(default=None, description="Rejected pieces.")
    ideal_cycle_time: float | None = Field(default=None, description="Time per piece at max speed.")
    ideal_rate: float | None = Field(default=None, description="Pieces per time unit at max speed.")


class DowntimeEvent(BaseModel):
    """One downtime event in an event log."""

    reason: str = Field(description="Reason for the stop.")
    duration: float = Field(description="Stop duration (same time unit as the runs).")
    planned: bool = Field(default=False, description="True for planned stops (setup, changeover).")


def _payload(result) -> dict:
    out = result.to_dict()
    out["summary"] = result.summary()
    return out


def _result(machine: MachineInput):
    return oee.oee(**machine.model_dump(exclude_none=True))


def _png(ax) -> bytes:
    import matplotlib.pyplot as plt

    buf = io.BytesIO()
    ax.figure.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                      facecolor="white")
    plt.close(ax.figure)
    return buf.getvalue()


def compute_oee(machine: MachineInput) -> dict:
    """OEE, the time waterfall and the six big losses from times and counts."""
    try:
        return _payload(_result(machine))
    except (ValueError, TypeError) as exc:
        return {"error": str(exc), "hint": "call describe_inputs for the fields and units"}


def oee_from_log(planned_production_time: float, runs: list[ProductionRun],
                 downtime_events: list[DowntimeEvent] | None = None,
                 all_time: float | None = None, startup_rejects: float | None = None,
                 target_oee: float = 0.85, name: str | None = None) -> dict:
    """OEE from an event log of production runs and downtime events."""
    try:
        result = oee.from_log(
            planned_production_time,
            runs=[r.model_dump(exclude_none=True) for r in runs],
            downtime_events=[e.model_dump() for e in downtime_events]
            if downtime_events else None,
            all_time=all_time, startup_rejects=startup_rejects,
            target_oee=target_oee, name=name)
        return _payload(result)
    except (ValueError, TypeError, KeyError) as exc:
        return {"error": str(exc), "hint": "call describe_inputs for the fields and units"}


def oee_from_factors(availability: float, performance: float, quality: float,
                     target_oee: float = 0.85, name: str | None = None) -> dict:
    """OEE from the three factors directly (each between 0 and 1)."""
    try:
        return _payload(oee.oee_from_factors(availability, performance, quality,
                                             target_oee=target_oee, name=name))
    except (ValueError, TypeError) as exc:
        return {"error": str(exc)}


def aggregate_oee(machines: list[MachineInput]) -> dict:
    """Roll OEE up across machines or shifts correctly (sums the buckets)."""
    try:
        results = [_result(m) for m in machines]
        rolled = oee.aggregate(results)
        out = _payload(rolled)
        out["machines"] = [{"name": r.name, "oee": r.oee} for r in results]
        return out
    except (ValueError, TypeError) as exc:
        return {"error": str(exc), "hint": "call describe_inputs for the fields and units"}


def describe_inputs() -> dict:
    """The input fields, units and OEE definitions, to format input correctly."""
    return {
        "sign_and_units": SIGN_AND_UNITS,
        "machine_fields": {n: f.description
                           for n, f in MachineInput.model_fields.items()},
        "definitions": DEFINITIONS,
        "six_big_losses": SIX_BIG_LOSSES,
    }


def waterfall_png(machine: MachineInput) -> bytes:
    return _png(oee.waterfall(_result(machine)))


def loss_pareto_png(machine: MachineInput) -> bytes:
    return _png(oee.losses_pareto(_result(machine)))


def trend_png(shifts: list[MachineInput]) -> bytes:
    return _png(oee.trend([_result(m) for m in shifts], factors=True))
