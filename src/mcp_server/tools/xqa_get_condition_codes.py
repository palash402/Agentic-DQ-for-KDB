"""MCP tool: xqa_get_condition_codes

Returns exchange condition code definitions for a venue. Condition codes
appear in the `code` column of the trade table and indicate special trade
circumstances (e.g. auction, odd-lot, negotiated deal, crossing).

Understanding condition codes is required for:
  - Correctly classifying auction vs continuous trades
  - Excluding special trades from outlier detection
  - Interpreting crossed quotes in context
"""

import logging
from typing import Any

from mcp_server.utils.kdbx import get_kdb_connection

logger = logging.getLogger(__name__)


async def xqa_get_condition_codes_impl(venue_code: str) -> dict[str, Any]:
    try:
        logger.info("xqa_get_condition_codes: venue_code=%s", venue_code)
        conn = get_kdb_connection()
        result = conn(
            f"select code,description,category from conditionCodes "
            f"where venue=`{venue_code}"
        )
        records = result.pd().to_dict(orient="records")
        # Ensure string serialisation
        serialised = [{k: str(v) for k, v in row.items()} for row in records]
        return {
            "status": "success",
            "venue": venue_code,
            "condition_codes": serialised,
            "count": len(serialised),
        }
    except Exception as exc:
        logger.error("xqa_get_condition_codes failed: %s", exc)
        return {"status": "error", "message": str(exc)}


def register_tools(mcp_server: Any) -> list[str]:

    @mcp_server.tool()
    async def xqa_get_condition_codes(venue_code: str) -> dict[str, Any]:
        """Returns exchange condition code definitions for a venue.

        Condition codes appear in the `code` column of the trade table.
        Reference this before interpreting individual trade records — codes
        indicate auction, odd-lot, negotiated, or other special trade types
        that require different DQ treatment from continuous session trades.

        Args:
            venue_code: Exchange MIC code, e.g. XTKS for Tokyo Stock Exchange.

        Returns:
            {
              "venue": str,
              "condition_codes": list[{"code": str, "description": str, "category": str}],
              "count": int
            }
        """
        return await xqa_get_condition_codes_impl(venue_code)

    return ["xqa_get_condition_codes"]
