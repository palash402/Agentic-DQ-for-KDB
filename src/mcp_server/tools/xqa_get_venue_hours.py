"""MCP tool: xqa_get_venue_hours

Returns venue trading session boundaries, auction timings, and UTC offset.
This is the most critical tool — call it before any completeness or timestamp
check to understand the expected trading windows and convert to storage timezone.

The storage timezone may differ from venue local time. For TSE:
  Venue local: JST (UTC+9)
  Storage timezone: JST-1h (UTC+8)
  TSE open 09:00 JST = 08:00 in stored data
"""

import logging
from typing import Any

from mcp_server.utils.kdbx import get_kdb_connection

logger = logging.getLogger(__name__)


async def xqa_get_venue_hours_impl(venue_code: str) -> dict[str, Any]:
    try:
        logger.info("xqa_get_venue_hours: venue_code=%s", venue_code)
        conn = get_kdb_connection()
        result = conn(
            f"select venue,date,tradingStart,tradingEnd,lunchStart,lunchEnd,utcOffset "
            f"from venueMap where venue=`{venue_code},date=max date"
        )
        records = result.pd().to_dict(orient="records")
        if not records:
            return {
                "status": "error",
                "message": f"No venue hours found for {venue_code}",
            }
        # Serialise time/date values to strings for JSON transport
        serialised = []
        for row in records:
            serialised.append({k: str(v) for k, v in row.items()})
        return {"status": "success", "venue": venue_code, "hours": serialised}
    except Exception as exc:
        logger.error("xqa_get_venue_hours failed: %s", exc)
        return {"status": "error", "message": str(exc)}


def register_tools(mcp_server: Any) -> list[str]:

    @mcp_server.tool()
    async def xqa_get_venue_hours(venue_code: str) -> dict[str, Any]:
        """Returns trading session hours, auction timings, and UTC offset for a venue.

        ALWAYS call this before applying any time-based filters in DQ checks.
        The data is stored in a storage timezone (often UTC+8 for Japanese exchanges)
        that differs from venue local time (JST = UTC+9). This tool provides the
        offset so you can correctly map venue hours to stored data timestamps.

        Returned fields:
          tradingStart / tradingEnd — full trading day boundaries (storage tz)
          lunchStart / lunchEnd     — lunch break boundaries (storage tz)
          utcOffset                 — storage timezone offset from UTC (hours)

        Args:
            venue_code: Exchange MIC code, e.g. XTKS for Tokyo Stock Exchange.

        Returns:
            {"status": "success", "venue": str, "hours": list[dict]}
        """
        return await xqa_get_venue_hours_impl(venue_code)

    return ["xqa_get_venue_hours"]
