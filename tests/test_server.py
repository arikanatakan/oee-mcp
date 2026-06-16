def test_server_imports_and_wires():
    from oee_mcp import server

    assert server.mcp is not None
    assert callable(server.main)


def test_all_tools_registered():
    import asyncio

    from oee_mcp import server

    names = {tool.name for tool in asyncio.run(server.mcp.list_tools())}
    expected = {
        "compute_oee", "oee_from_log", "oee_from_factors", "aggregate_oee",
        "describe_inputs", "waterfall_chart", "loss_pareto_chart", "trend_chart",
    }
    assert expected <= names
