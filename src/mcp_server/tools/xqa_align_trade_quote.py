"""MCP tool: xqa_align_trade_quote

Wraps q's `aj` (asof join) to align each trade with its immediately preceding
quote. Returns alignment statistics and a sample of aligned rows.

A trade is "aligned" when trade price == bid OR trade price == ask at the
quote timestamp immediately before the trade. Poor alignment indicates:
  - Feed latency (quote updates not arriving before trade reports)
  - Data quality issues in the quote feed
  - High-volatility windows where quotes move faster than trades report

Quote-to-trade ratios > 50:1 in any window indicate latency risk zones.
"""

import logging
from typing import Any

from mcp_server.utils.kdbx import get_kdb_connection

logger = logging.getLogger(__name__)


async def xqa_align_trade_quote_impl(
    date: str,
    sym: str,
    sample_rows: int = 20,
) -> dict[str, Any]:
    try:
        logger.info("xqa_align_trade_quote: date=%s sym=%s", date, sym)
        conn = get_kdb_connection()

        # aj[`sym`time; tradeTable; quoteTable]
        # Joins each trade to the quote with the largest time <= trade time
        result = conn(
            f"aj[`sym`time;"
            f"select sym,time,price,size,code,flag from trade "
            f"  where date={date},sym=`{sym};"
            f"select sym,time,bid,ask,bsize,asize from quote "
            f"  where date={date},sym=`{sym}]"
        )
        df = result.pd()

        if df.empty:
            return {
                "status": "success",
                "sym": sym,
                "date": date,
                "total_trades": 0,
                "message": "No trades found for this sym/date",
            }

        # Alignment: price should equal bid or ask at time of trade
        price = df["price"]
        bid = df["bid"]
        ask = df["ask"]
        aligned_mask = (price == bid) | (price == ask)
        n_aligned = int(aligned_mask.sum())
        total = len(df)

        # Quote-to-trade ratio for this sym/day
        quote_count_result = conn(
            f"count select from quote where date={date},sym=`{sym}"
        )
        quote_count = int(quote_count_result.py())
        qt_ratio = round(quote_count / max(total, 1), 2)

        # Sample of misaligned rows (most informative for diagnosis)
        misaligned_sample = (
            df[~aligned_mask][["time", "price", "bid", "ask", "size"]]
            .head(sample_rows)
            .to_dict(orient="records")
        )

        return {
            "status": "success",
            "sym": sym,
            "date": date,
            "total_trades": total,
            "aligned": n_aligned,
            "alignment_pct": round(100 * n_aligned / total, 2),
            "quote_count": quote_count,
            "quote_to_trade_ratio": qt_ratio,
            "latency_risk": qt_ratio > 50,
            "misaligned_sample": misaligned_sample,
        }
    except Exception as exc:
        logger.error("xqa_align_trade_quote failed: %s", exc)
        return {"status": "error", "message": str(exc)}


def register_tools(mcp_server: Any) -> list[str]:

    @mcp_server.tool()
    async def xqa_align_trade_quote(
        date: str,
        sym: str,
        sample_rows: int = 20,
    ) -> dict[str, Any]:
        """Aligns trades to quotes using q's asof join (aj) and returns alignment statistics.

        For each trade, finds the quote with the largest timestamp <= trade timestamp
        (the "prevailing" quote). Reports what percentage of trades have a price that
        matches the prevailing bid or ask.

        Also computes the quote-to-trade ratio for the symbol/date. Ratios > 50:1
        indicate latency risk zones where alignment is expected to degrade.

        Args:
            date: Analysis date in KDB+ date format, e.g. 2024.05.08
            sym: Symbol identifier, e.g. 7203.T
            sample_rows: Number of misaligned rows to return in the sample (default 20)

        Returns:
            {
              "total_trades": int,
              "aligned": int,
              "alignment_pct": float,
              "quote_count": int,
              "quote_to_trade_ratio": float,
              "latency_risk": bool,         # True if ratio > 50
              "misaligned_sample": list[dict]
            }
        """
        return await xqa_align_trade_quote_impl(date, sym, sample_rows)

    return ["xqa_align_trade_quote"]
