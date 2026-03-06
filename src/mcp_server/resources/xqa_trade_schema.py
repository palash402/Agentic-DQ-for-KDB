"""MCP resource: xqa_trade_schema

Schema and column definitions for the trade table.
Claude reads this resource to avoid malformed queries against the
date-partitioned tick table.
"""

from typing import Any


async def xqa_trade_schema_impl() -> str:
    return """
# trade table — schema reference

## Columns

| Column | Type   | Description |
|--------|--------|-------------|
| date   | date   | **Partition key** — must be included in every WHERE clause |
| sym    | symbol | Instrument identifier, e.g. `` `7203.T `` |
| time   | time   | Event timestamp in **storage timezone** (see timezone note) |
| price  | float  | Trade price in local currency |
| size   | long   | Trade size in shares (lot-adjusted) |
| code   | symbol | Exchange condition code (see xqa_get_condition_codes) |
| flag   | symbol | Auction flag: `` `opening ``, `` `closing ``, or null for continuous trades |

## Timezone note

Data is stored in the **storage timezone**, which may differ from venue local time.

For Tokyo Stock Exchange (XTKS):
- Venue local time: JST (UTC+9)
- Storage timezone: JST−1h = **UTC+8**
- TSE opens 09:00 JST → stored as **08:00**
- TSE lunch 11:30–12:30 JST → stored as **10:30–11:30**
- TSE closes 15:00 JST → stored as **14:00**

Always call `xqa_get_venue_hours` to get the exact offset before filtering by time.

## Partitioning

The table is **date-partitioned**. Every query MUST include `date=YYYY.MM.DD`
in the WHERE clause. Omitting date causes a full HDB scan and will timeout.

```q
/ Correct — scoped to a single partition
select count i from trade where date=2024.05.08, sym in syms

/ WRONG — never do this on a production HDB
select count i from trade where sym in syms
```

## Sampling warning

Do NOT sample this table. The AI must use ALL data for accurate DQ results.
Prompt instruction: "Use ALL data, no sampling".

## Auction trades

Auction trades are identified by the `flag` column:
- `` `opening `` — opening auction (concentrated execution at market open)
- `` `closing `` — closing auction (concentrated execution at market close)
- null — continuous session trade

Auction trades typically have:
- Larger average size than continuous session trades
- Concentrated timestamps (all within a 1-second window)
- Count approximately equal to the number of listed symbols

## Validation rules

| Column | Valid range | Invalid condition |
|--------|-------------|-------------------|
| price  | > 0         | null or negative price |
| size   | > 0         | null or negative size |
| flag   | null, `` `opening ``, `` `closing `` | any other symbol value |
"""


def register_resources(mcp_server: Any) -> list[str]:

    @mcp_server.resource("kdbx://xqa-trade-schema")
    async def xqa_trade_schema() -> str:
        """Schema, column definitions, timezone notes, and validation rules for the trade table."""
        return await xqa_trade_schema_impl()

    return ["xqa_trade_schema"]
