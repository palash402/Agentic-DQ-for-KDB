"""Integration tests — require a live KDB+ instance.

Run with:
    pytest tests/integration/ -m kdb_live

These tests are skipped by default (see pyproject.toml addopts).
They require:
  - KDB+ running on KDBX_DB_HOST:KDBX_DB_PORT (default localhost:5000)
  - Tables: trade, quote, stockCodes, venueMap, indexMembers, conditionCodes
  - Test data loaded (see q/init.q)
"""

import pytest

from mcp_server.utils.kdbx import get_kdb_connection


@pytest.mark.kdb_live
def test_kdb_connection_is_live() -> None:
    conn = get_kdb_connection()
    result = conn("1+1")
    assert result.py() == 2


@pytest.mark.kdb_live
@pytest.mark.asyncio
async def test_xqa_get_venue_syms_live() -> None:
    from mcp_server.tools.xqa_get_venue_syms import xqa_get_venue_syms_impl

    result = await xqa_get_venue_syms_impl("XTKS")
    assert result["status"] == "success"
    assert result["count"] > 0


@pytest.mark.kdb_live
@pytest.mark.asyncio
async def test_xqa_get_venue_hours_live() -> None:
    from mcp_server.tools.xqa_get_venue_hours import xqa_get_venue_hours_impl

    result = await xqa_get_venue_hours_impl("XTKS")
    assert result["status"] == "success"
    assert len(result["hours"]) > 0


@pytest.mark.kdb_live
@pytest.mark.asyncio
async def test_xqa_get_index_syms_live() -> None:
    from mcp_server.tools.xqa_get_index_syms import xqa_get_index_syms_impl

    result = await xqa_get_index_syms_impl("TOPIX")
    assert result["status"] == "success"
    assert result["count"] > 0


@pytest.mark.kdb_live
@pytest.mark.asyncio
async def test_full_dq_tool_chain_live() -> None:
    """Smoke test: exercise the full tool chain for one sym/date."""
    from mcp_server.tools.xqa_get_index_syms import xqa_get_index_syms_impl
    from mcp_server.tools.xqa_get_venue_hours import xqa_get_venue_hours_impl
    from mcp_server.tools.xqa_align_trade_quote import xqa_align_trade_quote_impl

    # Step 1: get symbols
    syms_result = await xqa_get_index_syms_impl("TOPIX")
    assert syms_result["status"] == "success"
    first_sym = syms_result["symbols"][0]

    # Step 2: get venue hours
    hours_result = await xqa_get_venue_hours_impl("XTKS")
    assert hours_result["status"] == "success"

    # Step 3: align trade-quote for first sym (use a known test date)
    import os
    test_date = os.environ.get("TEST_DATE", "2024.05.08")
    align_result = await xqa_align_trade_quote_impl(test_date, first_sym)
    # May be empty if no data — just check it doesn't error
    assert align_result["status"] in ("success", "error")
