"""Template for creating new xqa_* MCP tools.

To add a new tool:
1. Copy this file: cp _template.py xqa_my_tool.py
2. Rename my_tool -> xqa_my_tool throughout
3. Implement the _impl function with your q query
4. Update the docstring — Claude selects tools based on the description

The server auto-discovers any .py file in this directory (except those starting
with _). No manual registration or imports needed — just restart the MCP client.
"""

import logging
from typing import Any

from mcp_server.utils.kdbx import get_kdb_connection

logger = logging.getLogger(__name__)


async def my_tool_impl(param1: str, param2: int) -> dict[str, Any]:
    """Implementation separated from registration for testability."""
    try:
        logger.info("my_tool called: param1=%s param2=%d", param1, param2)
        conn = get_kdb_connection()

        # Use conn("q expression") — not SQL, not conn.q()
        # Always scope queries with date partition for tick tables:
        #   result = conn(f"select ... from trade where date={param1},sym=`{param2}")
        result = conn(f"1+{param2}")  # placeholder

        return {"status": "success", "data": result.py()}
    except Exception as exc:
        logger.error("my_tool failed: %s", exc)
        return {"status": "error", "message": str(exc)}


def register_tools(mcp_server: Any) -> list[str]:
    """Called automatically by main.py at server startup."""

    @mcp_server.tool()
    async def my_tool(param1: str, param2: int) -> dict[str, Any]:
        """One-line summary of what this tool returns (Claude reads this to decide when to call it).

        Longer description: what data source, what filters, what the return structure looks like.

        Args:
            param1: description
            param2: description
        """
        return await my_tool_impl(param1, param2)

    return ["my_tool"]
