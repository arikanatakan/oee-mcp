"""The MCP server: registers the oee tools and runs over stdio.

All tools are pure, read-only computations, marked with annotations so a client
can present and auto-run them safely.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP, Image
from mcp.types import ToolAnnotations

from . import _tools
from ._tools import MachineInput

mcp = FastMCP("oee")


def _annotations(title: str) -> ToolAnnotations:
    return ToolAnnotations(
        title=title,
        readOnlyHint=True,
        idempotentHint=True,
        openWorldHint=False,
    )


mcp.tool(annotations=_annotations("Compute OEE"))(_tools.compute_oee)
mcp.tool(annotations=_annotations("OEE from an event log"))(_tools.oee_from_log)
mcp.tool(annotations=_annotations("OEE from the three factors"))(_tools.oee_from_factors)
mcp.tool(annotations=_annotations("Aggregate OEE across machines"))(_tools.aggregate_oee)
mcp.tool(annotations=_annotations("Describe the inputs"))(_tools.describe_inputs)


@mcp.tool(annotations=_annotations("OEE waterfall chart (PNG)"))
def waterfall_chart(machine: MachineInput) -> Image:
    """Render the OEE time waterfall (planned to fully productive) as a PNG."""
    return Image(data=_tools.waterfall_png(machine), format="png")


@mcp.tool(annotations=_annotations("Loss Pareto chart (PNG)"))
def loss_pareto_chart(machine: MachineInput) -> Image:
    """Render a Pareto of the six big losses as a PNG image."""
    return Image(data=_tools.loss_pareto_png(machine), format="png")


@mcp.tool(annotations=_annotations("OEE trend chart (PNG)"))
def trend_chart(shifts: list[MachineInput]) -> Image:
    """Render the OEE and A/P/Q trend over a sequence of results as a PNG."""
    return Image(data=_tools.trend_png(shifts), format="png")


def main() -> None:
    """Console-script entry point: run the server on stdio."""
    mcp.run()


if __name__ == "__main__":
    main()
