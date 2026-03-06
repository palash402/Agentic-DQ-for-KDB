"""MCP tool: xqa_get_venue_syms

Returns all symbol identifiers traded on a given venue. Use this before
scoping any DQ analysis to ensure symbol coverage is correct.
"""

import logging
from typing import Any

from mcp_server.utils.kdbx import get_kdb_connection

logger = logging.getLogger(__name__)


async def xqa_get_venue_syms_impl(venue_code: str) -> dict[str, Any]:
    try:
        logger.info("xqa_get_venue_syms: venue_code=%s", venue_code)
        conn = get_kdb_connection()
        result = conn(f"exec sym from stockCodes where venue=`{venue_code}")
        syms: list[str] = [str(s) for s in result.py()]
        return {"status": "success", "venue": venue_code, "symbols": syms, "count": len(syms)}
    except Exception as exc:
        logger.error("xqa_get_venue_syms failed: %s", exc)
        return {"status": "error", "message": str(exc)}


def register_tools(mcp_server: Any) -> list[str]:

    @mcp_server.tool()
    async def xqa_get_venue_syms(venue_code: str) -> dict[str, Any]:
        """Returns all symbol identifiers (e.g. 7203.T) traded on the given venue.

        Call this first to establish the full symbol universe before any DQ analysis.
        For index-scoped analysis prefer xqa_get_index_syms (smaller, focused list).

        Args:
            venue_code: Exchange MIC code, e.g. XTKS for Tokyo Stock Exchange.

        Returns:
            {"status": "success", "venue": str, "symbols": list[str], "count": int}
        """
        return await xqa_get_venue_syms_impl(venue_code)

    return ["xqa_get_venue_syms"]
