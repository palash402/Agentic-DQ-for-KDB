"""Unit tests for xqa_* MCP tools (no live KDB+ required)."""

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from tests.conftest import MockKdbConnection


# ---------------------------------------------------------------------------
# xqa_get_venue_syms
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_xqa_get_venue_syms_returns_list(mock_kdb: MockKdbConnection) -> None:
    mock_kdb.set_response("stockCodes", ["7203.T", "6758.T", "8306.T"])

    from mcp_server.tools.xqa_get_venue_syms import xqa_get_venue_syms_impl

    with patch("mcp_server.tools.xqa_get_venue_syms.get_kdb_connection", return_value=mock_kdb):
        result = await xqa_get_venue_syms_impl("XTKS")

    assert result["status"] == "success"
    assert result["venue"] == "XTKS"
    assert isinstance(result["symbols"], list)
    assert result["count"] == 3


@pytest.mark.asyncio
async def test_xqa_get_venue_syms_error_handling(mock_kdb: MockKdbConnection) -> None:
    mock_kdb.set_response("stockCodes", Exception("connection lost"))

    from mcp_server.tools.xqa_get_venue_syms import xqa_get_venue_syms_impl

    # Simulate connection error by making __call__ raise
    broken = MagicMock(side_effect=RuntimeError("KDB+ unreachable"))
    with patch("mcp_server.tools.xqa_get_venue_syms.get_kdb_connection", return_value=broken):
        result = await xqa_get_venue_syms_impl("XTKS")

    assert result["status"] == "error"
    assert "message" in result


# ---------------------------------------------------------------------------
# xqa_get_index_syms
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_xqa_get_index_syms_returns_constituents(mock_kdb: MockKdbConnection) -> None:
    mock_kdb.set_response("indexMembers", ["7203.T", "6758.T"])

    from mcp_server.tools.xqa_get_index_syms import xqa_get_index_syms_impl

    with patch("mcp_server.tools.xqa_get_index_syms.get_kdb_connection", return_value=mock_kdb):
        result = await xqa_get_index_syms_impl("TOPIX")

    assert result["status"] == "success"
    assert result["index"] == "TOPIX"
    assert result["count"] == 2


# ---------------------------------------------------------------------------
# xqa_get_venue_hours
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_xqa_get_venue_hours_returns_session_data(
    mock_kdb: MockKdbConnection,
    sample_venue_hours_df: pd.DataFrame,
) -> None:
    mock_kdb.set_response("venueMap", sample_venue_hours_df)

    from mcp_server.tools.xqa_get_venue_hours import xqa_get_venue_hours_impl

    with patch("mcp_server.tools.xqa_get_venue_hours.get_kdb_connection", return_value=mock_kdb):
        result = await xqa_get_venue_hours_impl("XTKS")

    assert result["status"] == "success"
    assert result["venue"] == "XTKS"
    assert len(result["hours"]) == 1
    assert result["hours"][0]["utcOffset"] == "8"


@pytest.mark.asyncio
async def test_xqa_get_venue_hours_not_found(mock_kdb: MockKdbConnection) -> None:
    mock_kdb.set_response("venueMap", pd.DataFrame())

    from mcp_server.tools.xqa_get_venue_hours import xqa_get_venue_hours_impl

    with patch("mcp_server.tools.xqa_get_venue_hours.get_kdb_connection", return_value=mock_kdb):
        result = await xqa_get_venue_hours_impl("UNKNOWN")

    assert result["status"] == "error"


# ---------------------------------------------------------------------------
# xqa_align_trade_quote
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_xqa_align_trade_quote_perfect_alignment(
    mock_kdb: MockKdbConnection,
    aligned_trade_quote_df: pd.DataFrame,
) -> None:
    mock_kdb.set_response("aj[", aligned_trade_quote_df)
    # quote count for ratio calculation
    quote_count_mock = MagicMock()
    quote_count_mock.py.return_value = len(aligned_trade_quote_df) * 10

    def mock_call(query: str, *args: object) -> MagicMock:
        if "aj[" in query:
            m = MagicMock()
            m.pd.return_value = aligned_trade_quote_df
            return m
        elif "count" in query:
            return quote_count_mock
        m = MagicMock()
        m.py.return_value = 0
        return m

    from mcp_server.tools.xqa_align_trade_quote import xqa_align_trade_quote_impl

    with patch("mcp_server.tools.xqa_align_trade_quote.get_kdb_connection") as mock_conn:
        mock_conn.return_value = MagicMock(side_effect=mock_call)
        result = await xqa_align_trade_quote_impl("2024.05.08", "7203.T")

    assert result["status"] == "success"
    assert result["alignment_pct"] == 100.0
    assert result["total_trades"] == len(aligned_trade_quote_df)


@pytest.mark.asyncio
async def test_xqa_align_trade_quote_empty_result(mock_kdb: MockKdbConnection) -> None:
    def mock_call(query: str, *args: object) -> MagicMock:
        m = MagicMock()
        m.pd.return_value = pd.DataFrame()
        m.py.return_value = 0
        return m

    from mcp_server.tools.xqa_align_trade_quote import xqa_align_trade_quote_impl

    with patch("mcp_server.tools.xqa_align_trade_quote.get_kdb_connection") as mock_conn:
        mock_conn.return_value = MagicMock(side_effect=mock_call)
        result = await xqa_align_trade_quote_impl("2024.05.08", "NOSYM.T")

    assert result["status"] == "success"
    assert result["total_trades"] == 0


# ---------------------------------------------------------------------------
# xqa_get_condition_codes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_xqa_get_condition_codes_returns_records(mock_kdb: MockKdbConnection) -> None:
    codes_df = pd.DataFrame([
        {"code": "A", "description": "Auction", "category": "auction"},
        {"code": "C", "description": "Continuous", "category": "continuous"},
    ])
    mock_kdb.set_response("conditionCodes", codes_df)

    from mcp_server.tools.xqa_get_condition_codes import xqa_get_condition_codes_impl

    with patch("mcp_server.tools.xqa_get_condition_codes.get_kdb_connection", return_value=mock_kdb):
        result = await xqa_get_condition_codes_impl("XTKS")

    assert result["status"] == "success"
    assert result["count"] == 2
    assert result["condition_codes"][0]["code"] == "A"


# ---------------------------------------------------------------------------
# Resource content smoke tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_trade_schema_resource_is_markdown() -> None:
    from mcp_server.resources.xqa_trade_schema import xqa_trade_schema_impl

    content = await xqa_trade_schema_impl()
    assert "trade table" in content
    assert "date" in content
    assert "sym" in content
    assert "partition" in content.lower()


@pytest.mark.asyncio
async def test_quote_schema_resource_mentions_crossed_quotes() -> None:
    from mcp_server.resources.xqa_quote_schema import xqa_quote_schema_impl

    content = await xqa_quote_schema_impl()
    assert "crossed" in content.lower()
    assert "bid" in content
    assert "ask" in content


@pytest.mark.asyncio
async def test_venue_guide_resource_mentions_timezone() -> None:
    from mcp_server.resources.xqa_venue_guide import xqa_venue_guide_impl

    content = await xqa_venue_guide_impl()
    assert "UTC" in content
    assert "JST" in content
    assert "auction" in content.lower()


# ---------------------------------------------------------------------------
# Prompt content smoke tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dq_analysis_prompt_contains_all_four_categories() -> None:
    from mcp_server.prompts.xqa_dq_analysis import xqa_dq_analysis_impl

    prompt = await xqa_dq_analysis_impl("2024.05.08", "TOPIX", "XTKS")
    assert "COMPLETENESS" in prompt
    assert "TIMESTAMP" in prompt
    assert "VALIDATION" in prompt
    assert "UNDERSTANDING" in prompt


@pytest.mark.asyncio
async def test_dq_analysis_prompt_includes_date_and_index() -> None:
    from mcp_server.prompts.xqa_dq_analysis import xqa_dq_analysis_impl

    prompt = await xqa_dq_analysis_impl("2024.05.08", "TOPIX", "XTKS")
    assert "2024.05.08" in prompt
    assert "TOPIX" in prompt
    assert "XTKS" in prompt
    assert "no sampling" in prompt.lower() or "NO sampling" in prompt
