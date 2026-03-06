"""MCP tool: xqa_get_index_syms

Returns index constituent symbols. Scoping DQ analysis to an index (e.g. TOPIX
top 50) rather than all venue symbols keeps queries fast and focused on the
most liquid, representative instruments.
"""

import logging
from typing import Any

from mcp_server.utils.kdbx import get_kdb_connection

logger = logging.getLogger(__name__)


async def xqa_get_index_syms_impl(index_name: str) -> dict[str, Any]:
    try:
        logger.info("xqa_get_index_syms: index_name=%s", index_name)
        conn = get_kdb_connection()
        result = conn(f"exec sym from indexMembers where index=`{index_name}")
        syms: list[str] = [str(s) for s in result.py()]
        return {"status": "success", "index": index_name, "symbols": syms, "count": len(syms)}
    except Exception as exc:
        logger.error("xqa_get_index_syms failed: %s", exc)
        return {"status": "error", "message": str(exc)}


def register_tools(mcp_server: Any) -> list[str]:

    @mcp_server.tool()
    async def xqa_get_index_syms(index_name: str) -> dict[str, Any]:
        """Returns the constituent symbols for the given index (e.g. TOPIX, NIKKEI225).

        Use this to scope DQ analysis to a representative subset of liquid symbols
        rather than the entire venue. This makes queries faster and results more
        actionable (index constituents are the highest-quality data to check first).

        Args:
            index_name: Index identifier, e.g. TOPIX, NIKKEI225.

        Returns:
            {"status": "success", "index": str, "symbols": list[str], "count": int}
        """
        return await xqa_get_index_syms_impl(index_name)

    return ["xqa_get_index_syms"]
