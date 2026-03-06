"""MCP resource: xqa_quote_schema

Schema and column definitions for the quote table.
Includes bid/ask semantics, crossed-quote rules, and auction period behaviour.
"""

from typing import Any


async def xqa_quote_schema_impl() -> str:
    return """
# quote table — schema reference

## Columns

| Column | Type   | Description |
|--------|--------|-------------|
| date   | date   | **Partition key** — must be in every WHERE clause |
| sym    | symbol | Instrument identifier, e.g. `` `7203.T `` |
| time   | time   | Quote timestamp in storage timezone |
| ask    | float  | Best ask price (lowest offer) |
| asize  | long   | Ask size (shares available at ask) |
| bid    | float  | Best bid price (highest bid) |
| bsize  | long   | Bid size (shares available at bid) |

## Normal market condition

During continuous trading, a valid quote satisfies:
```
bid < ask   (spread > 0)
bid > 0
ask > 0
bsize > 0
asize > 0
```

## Crossed quote definition

A **crossed quote** occurs when `bid >= ask`. This should NOT happen during
continuous trading and indicates:
- Feed error or out-of-sequence message
- Locked market (bid == ask) — unusual but possible
- Data quality issue

**Exception:** Crossed quotes ARE expected during auction periods
(pre-open and closing auction windows) due to TSE's special quotation mechanism,
where the indicative auction price may cause temporary crossing.

Always filter to continuous trading hours before flagging crossed quotes.
Use `xqa_get_venue_hours` to determine the exact continuous session windows.

## Timezone

Same as trade table — storage timezone, not venue local time.
For XTKS: UTC+8 (JST−1h).

## Partitioning

Always include `date=YYYY.MM.DD` in every query. Same rule as trade table.

## Quote-to-trade ratio

A healthy market typically shows:
- 5:1 to 20:1 quote-to-trade ratio during continuous hours
- > 50:1 ratio indicates a latency risk zone (high quote activity vs trades)
- Compute via: `xqa_align_trade_quote` for per-symbol analysis

## Validation rules

| Column | Valid range (continuous trading) | Invalid condition |
|--------|----------------------------------|-------------------|
| bid    | > 0                              | null or <= 0 |
| ask    | > 0                              | null or <= 0 |
| bsize  | > 0                              | null or <= 0 |
| asize  | > 0                              | null or <= 0 |
| spread | ask - bid > 0                   | crossed: bid >= ask |
"""


def register_resources(mcp_server: Any) -> list[str]:

    @mcp_server.resource("kdbx://xqa-quote-schema")
    async def xqa_quote_schema() -> str:
        """Schema, bid/ask semantics, crossed-quote rules, and validation guide for the quote table."""
        return await xqa_quote_schema_impl()

    return ["xqa_quote_schema"]
