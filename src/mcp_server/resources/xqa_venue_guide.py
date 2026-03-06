"""MCP resource: xqa_venue_guide

Domain knowledge guide covering venue trading sessions, auction mechanics,
timezone handling, and DQ interpretation rules.

This is the AI's reference for understanding WHY certain patterns appear
in the data and whether they are genuine issues or expected behaviour.
"""

from typing import Any


async def xqa_venue_guide_impl() -> str:
    return """
# Venue & Auction Domain Knowledge Guide

## Why venue hours matter for DQ

Data quality checks must be scoped to the correct trading windows.
Querying the full day will include pre-open periods (sparse data),
lunch breaks (zero data), and post-close (low volume) — all of which
look like "gaps" but are expected. Always:

1. Call `xqa_get_venue_hours` before any completeness or timestamp check
2. Filter queries to the relevant session (morning / afternoon)
3. Exclude lunch break from gap detection

---

## Tokyo Stock Exchange (XTKS) — session structure

All times below are in **storage timezone (UTC+8 = JST−1h)**.
Tokyo local time (JST) = storage time + 1 hour.

| Session | Storage time | JST (local) | Expected data |
|---------|-------------|-------------|---------------|
| Pre-open / order input | 07:00–08:00 | 08:00–09:00 | Sparse quote updates only |
| Opening auction | ~08:00 | ~09:00 | Concentrated trade burst |
| Morning continuous | 08:00–10:30 | 09:00–11:30 | High density trades + quotes |
| Lunch break | 10:30–11:30 | 11:30–12:30 | Zero trades (expected gap) |
| Afternoon continuous | 11:30–14:00 | 12:30–15:00 | High density trades + quotes |
| Closing auction | ~13:55–14:00 | ~14:55–15:00 | Concentrated trade burst |
| Post-close / ToSTNeT | 14:00–15:00 | 15:00–16:00 | Low volume negotiated trades |

---

## Auction classification

Opening and closing auctions produce a single batch of executions.
They are identified by the `flag` column in the trade table:
- `` `opening `` — opening auction trade
- `` `closing `` — closing auction trade
- null — continuous session trade

**Expected characteristics of auction trades:**
- Timestamp concentration: all execution within a ~1-second window
- Count: approximately equal to the number of symbols with orders at the auction
- Average size: significantly larger than continuous trades (accumulated orders)

**To verify auction classification:**
```q
/ Check opening auction count vs expected symbol count
select count i, avg size by flag from trade
where date=2024.05.08, sym in syms
```

---

## TSE special quotation mechanism (crossed quotes)

During auction periods, the exchange publishes an **indicative auction price**
(特別気配 — special quotation) that can cause the displayed bid >= ask.
This is intentional and reflects the accumulated buy/sell imbalance.

**Rule:**
- Crossed quotes (bid >= ask) during **continuous trading** = DQ issue
- Crossed quotes during **auction windows** = expected, not a DQ issue

Always filter to continuous hours before reporting crossed quote counts.

---

## Timezone conversion cheat sheet (XTKS)

```
Storage time    →  JST (venue local)
07:00           →  08:00
08:00           →  09:00  ← market open
09:00           →  10:00
10:30           →  11:30  ← lunch start
11:30           →  12:30  ← afternoon start
13:55           →  14:55  ← closing auction begins
14:00           →  15:00  ← market close
```

In q queries, apply the offset as:
```q
/ Convert UTC+8 storage time to JST (+1h):
jst_time: time + 01:00:00.000

/ Or filter using storage timezone directly (recommended):
select from trade where date=2024.05.08, time within (08:00:00;10:30:00)
```

---

## Reference table: stockCodes

Contains the master instrument list. Columns include:
- `sym` — trading symbol (matches trade/quote tables)
- `isin` — ISIN code (may be shared across cross-listings)
- `name` — company name
- `venue` — primary trading venue MIC
- `sector` — TOPIX sector classification

**Duplicate handling:**
- Duplicate ISIN may indicate cross-listings or ETF share classes — not necessarily errors
- Always confirm AI duplicate explanations with a domain expert

---

## Reference table: venueMap

Contains venue configuration history. Columns include:
- `venue` — Exchange MIC code
- `date` — effective date of the configuration
- `tradingStart` / `tradingEnd` — full trading day boundaries
- `lunchStart` / `lunchEnd` — lunch break (if applicable)
- `utcOffset` — storage timezone offset from UTC

Multiple rows per venue = operating hours changes over time (valid, not duplicates).

---

## Prompt engineering reminders

| Check | Required instruction |
|-------|---------------------|
| Any time filter | Call `xqa_get_venue_hours` first |
| Gap detection | "Check 1-minute bins explicitly" |
| Crossed quotes | "Filter to continuous hours only" |
| Null/negative check | "Use ALL data, no sampling" |
| Outlier detection | "Provide context ±30 seconds around outlier" |
| Auction classification | "Cross-check flag column counts vs symbol count" |
"""


def register_resources(mcp_server: Any) -> list[str]:

    @mcp_server.resource("kdbx://xqa-venue-guide")
    async def xqa_venue_guide() -> str:
        """Domain knowledge: venue sessions, auction mechanics, timezone conversion, DQ rules."""
        return await xqa_venue_guide_impl()

    return ["xqa_venue_guide"]
