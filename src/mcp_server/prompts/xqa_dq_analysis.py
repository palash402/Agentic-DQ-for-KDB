"""MCP prompt: xqa_dq_analysis

Generates a scoped, structured DQ analysis prompt for a specific date,
index, and venue. Covers all four DQ categories from the ExeQution Analytics
whitepaper: Completeness, Timestamp Consistency, Validation, Understanding.

Parameters:
  date  — analysis date (KDB+ format: YYYY.MM.DD)
  index — index name (e.g. TOPIX)
  venue — exchange MIC code (e.g. XTKS)
"""

from typing import Any


async def xqa_dq_analysis_impl(date: str, index: str, venue: str) -> str:
    return f"""
SCOPE
─────
- Time period : ONLY USE DATA FOR {date}. DO NOT LOOK AT ANY OTHER DATES.
- Symbols     : use the {index} index constituents — call xqa_get_index_syms("{index}") first.
- trade table : date (partition), sym, time, price, size, code, flag
- quote table : date (partition), sym, time, ask, asize, bid, bsize

MANDATORY SETUP (do these before any analysis)
───────────────────────────────────────────────
1. Call xqa_get_index_syms("{index}") → save as `syms`
2. Call xqa_get_venue_hours("{venue}") → save session boundaries and utcOffset
3. All time filters must use storage timezone times from step 2 (NOT venue local time)

─────────────────────────────────────────────────────────────────────────────
DQ CHECK 1 — DATA COMPLETENESS
─────────────────────────────────────────────────────────────────────────────
Q1a. How many trade records exist for {date} for {index} symbols?
     Break down by trading session (pre-open, morning, lunch, afternoon, post-close)
     using the session boundaries from xqa_get_venue_hours.
     Report: row count per session, total, and % of total for each.

Q1b. How many quote records exist for {date}?
     Same session breakdown as Q1a.

Q1c. Are any {index} symbols completely missing from trade data on {date}?
     List any symbols with zero trades.

Q1d. Are any {index} symbols completely missing from quote data on {date}?

─────────────────────────────────────────────────────────────────────────────
DQ CHECK 2 — TIMESTAMP CONSISTENCY
─────────────────────────────────────────────────────────────────────────────
Q2a. Bin trade records into 1-MINUTE intervals across the full trading day.
     Flag every minute with ZERO trades during continuous trading hours
     (morning session + afternoon session, excluding lunch break and auction windows).
     List each gap minute explicitly.

Q2b. Same analysis for quote data — 1-minute bins, flag zero-quote minutes.

Q2c. Cross-reference any gaps against the auction schedule from xqa_get_venue_hours.
     A gap that coincides with an auction window is expected. A gap in the middle
     of a continuous session is a DQ issue.

─────────────────────────────────────────────────────────────────────────────
DQ CHECK 3 — DATA VALIDATION
─────────────────────────────────────────────────────────────────────────────
Q3a. Count null values in trade.price and trade.size for {date}.
     Report count and percentage of total records.

Q3b. Count negative values in trade.price and trade.size for {date}.

Q3c. Count null values in quote.bid, quote.ask, quote.bsize, quote.asize.

Q3d. Count negative values in quote.bid, quote.ask, quote.bsize, quote.asize.

Q3e. Count CROSSED QUOTES (bid >= ask) during CONTINUOUS TRADING HOURS ONLY.
     (Exclude pre-open and auction windows — crossed quotes are expected there.)
     Report count and % of total continuous-session quotes.

Q3f. Detect price outliers in trade data:
     Flag any trade where price deviates > 5 standard deviations from the
     30-trade rolling average for that symbol.
     For each outlier found, show the ±5 trades surrounding it for context.

─────────────────────────────────────────────────────────────────────────────
DQ CHECK 4 — DATA UNDERSTANDING
─────────────────────────────────────────────────────────────────────────────
Q4a. Verify auction trade classification:
     - How many trades have flag=`opening? flag=`closing? flag=null?
     - Does the opening auction count approximately match the number of {index} symbols?
     - Are opening auction trades concentrated within a 1-second window at market open?
     - Are closing auction trades concentrated at market close?

Q4b. Trade-quote alignment:
     Call xqa_align_trade_quote for a sample of 5 {index} symbols.
     For each: report alignment_pct and quote_to_trade_ratio.
     Flag any symbol with alignment_pct < 80% or quote_to_trade_ratio > 50.

Q4c. Identify latency risk zones:
     Compute quote-to-trade ratio in 30-minute windows across the trading day.
     Flag any window where ratio > 50:1.

─────────────────────────────────────────────────────────────────────────────
OUTPUT FORMAT
─────────────────────────────────────────────────────────────────────────────
For each finding produce a structured entry:

  Category  : [Completeness | Timestamp | Validation | Understanding]
  Severity  : [INFO | WARNING | CRITICAL]
  Finding   : <one sentence>
  Evidence  : <row counts, percentages, specific timestamps or symbols>
  Rows used : <how many rows were analysed — confirms no sampling>
  Action    : <recommended next step>

End with an Executive Summary: total findings by severity, and the most
critical issue requiring immediate investigation.

─────────────────────────────────────────────────────────────────────────────
CONSTRAINTS (MUST FOLLOW)
─────────────────────────────────────────────────────────────────────────────
- Use ALL data — NO sampling of any kind
- Every query MUST include date={date} (date-partitioned table)
- Do NOT query other dates
- For time filters, always use storage timezone (from xqa_get_venue_hours)
- For each finding, state the exact row count analysed
"""


def register_prompts(mcp_server: Any) -> list[str]:

    @mcp_server.prompt()
    async def xqa_dq_analysis(date: str, index: str, venue: str) -> str:
        """Full DQ analysis prompt for a specific date, index, and venue.

        Covers all four DQ categories from the ExeQution Analytics whitepaper:
        Completeness, Timestamp Consistency, Validation, and Data Understanding.

        Args:
            date:  Analysis date in KDB+ format, e.g. 2024.05.08
            index: Index name, e.g. TOPIX
            venue: Exchange MIC code, e.g. XTKS
        """
        return await xqa_dq_analysis_impl(date, index, venue)

    return ["xqa_dq_analysis"]
