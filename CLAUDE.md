# CLAUDE.md — Agentic DQ for KDB

This file provides guidance for AI assistants (Claude and others) working in this repository. It documents the project's purpose, architecture, conventions, and development workflows.

**Reference whitepaper:** [Agentic Workflow for Data Quality — ExeQution Analytics](https://exequtionanalytics.com/wp-content/uploads/2026/01/Agentic-Workflow-for-Data-Quality.pdf)
**MCP Server source:** [KxSystems/kdb-x-mcp-server](https://github.com/KxSystems/kdb-x-mcp-server)
**Official docs:** [code.kx.com/kdb-x/integrations/mcp-server](https://code.kx.com/kdb-x/integrations/mcp-server.html)

---

## Project Overview

**Agentic-DQ-for-KDB** is an AI-agent-driven **Data Quality (DQ)** framework targeting **KDB+/q** (KDB-X) databases. It uses **MCP (Model Context Protocol)** to connect Claude to KDB-X, enabling natural-language-driven data quality checks without writing pre-defined q queries for every check.

The project is inspired directly by ExeQution Analytics' research demonstrating that AI agents — given the right MCP tools, resources, and prompts — can autonomously detect data completeness gaps, timestamp inconsistencies, bad data points, anomalies, outliers, duplicates, and trade-quote misalignment in high-frequency financial market data.

### Goals

- Use Claude + KDB-X MCP Server to perform DQ checks via natural language prompts
- Build reusable q-language tool wrappers as MCP tools (preferred over SQL for performance)
- Provide rich context via MCP resources (table schemas, venue hours, index constituents)
- Automate the four DQ check categories: Completeness, Timestamp Consistency, Validation, Understanding
- Reduce the burden on development teams maintaining bespoke DQ query libraries
- Always pair AI analysis with human domain-expert verification checkpoints

### Validated DQ Check Categories (from whitepaper)

| Category | What it checks |
|---|---|
| **Data Completeness** | Gaps in data, distribution across trading sessions vs. venue hours |
| **Timestamp Consistency** | Temporal gaps (30-min and 3-min granularity), event ordering vs. venue schedule |
| **Data Validation** | Null/negative values, crossed quotes (bid > ask), price/size outliers, duplicate reference data |
| **Data Understanding** | Auction trade classification, trade-quote alignment via `aj`, latency risk zones |

---

## Repository State

> **Status: Early-stage / skeleton.** As of the initial commit, only `README.md` and `LICENSE` exist. Source code, configuration, and tests are yet to be added. This CLAUDE.md serves as the authoritative guide for how the project should be structured as it evolves.

---

## Architecture: MCP-Based Agentic DQ

```
Claude Desktop (natural language client)
    │
    │  natural language prompts
    ▼
KDB-X MCP Server  (uv run mcp-server, default port 8000)
    ├── TOOLS      → Python files in src/mcp_server/tools/  (auto-discovered)
    ├── RESOURCES  → Python files in src/mcp_server/resources/ (auto-discovered)
    └── PROMPTS    → Python files in src/mcp_server/prompts/  (auto-discovered)
    │
    │  q IPC (pykx)
    ▼
KDB-X / KDB+ process  (default port 5000)
    └── trade, quote, stockCodes, venueMap tables
```

MCP is a standardised communication framework — like HTTP for web pages, or FIX for orders, but for AI context. It moves metadata about how a model should interpret data and produce results.

### Three MCP Concepts

| Concept | Role | How to extend |
|---|---|---|
| **Tools** | Python functions that query the database and return structured data | Add a `.py` file to `src/mcp_server/tools/` |
| **Resources** | Text/script files providing context the AI reads (schemas, guidance) | Add a `.py` file to `src/mcp_server/resources/` |
| **Prompts** | Auto-generated reusable prompt templates for common tasks | Add a `.py` file to `src/mcp_server/prompts/` |

All three are **auto-discovered at server startup** — no manual registration or imports required. Restart the MCP client after adding a new file.

### Built-in KDB-X MCP Tools (from KX)

| Name | Type | Purpose |
|---|---|---|
| `kdbx_run_sql_query` | Tool | Execute read-only SELECT queries (1000-row cap, blocks INSERT/DROP/DELETE) |
| `kdbx_similarity_search` | Tool | Vector similarity search (KDB-X only) |
| `kdbx_hybrid_search` | Tool | Combined vector + text search (KDB-X only) |
| `kdbx_describe_tables` | Resource | Overview of all tables with schema and data preview |
| `kdbx_sql_query_guidance` | Resource | SQL syntax rules, best practices, examples |
| `kdbx_table_analysis` | Prompt | Dynamic prompt template for deep-dive table analysis |

> **Important:** `kdbx_run_sql_query` is flexible but **slow** on millions of tick records. Prefer custom q-language tool wrappers for performance-sensitive DQ checks.

### Custom Tools to Build

Follow the `xqa_` prefix convention for project-specific tools:

| Tool name | Purpose |
|---|---|
| `xqa_get_venue_syms` | Returns all symbols traded on a specific venue |
| `xqa_get_index_syms` | Returns index constituents (e.g., TOPIX top 50) for scoped analysis |
| `xqa_get_venue_hours` | Returns venue trading hours and timezone offset config |
| `xqa_align_trade_quote` | Wraps q's `aj` function for trade-quote timestamp alignment |
| `xqa_get_condition_codes` | Returns exchange condition code definitions |

New tools should provide **general-purpose context** (venue metadata, schema info, symbol lists), not encode specific DQ check logic. General tools are reusable; AI generates check logic dynamically.

---

## Expected Technology Stack

| Layer | Technology |
|---|---|
| Database | KDB-X / KDB+/q |
| MCP Server | [KDB-X MCP Server](https://github.com/KxSystems/kdb-x-mcp-server) by KX |
| AI client | Claude Desktop (connects via streamable-http transport) |
| Python runtime | Python 3.11+ managed with `uv` |
| KDB+ Python bridge | `pykx` (used internally by the MCP server) |
| q tool wrappers | Native q language (not SQL) for performance |
| Config | `.env` file + Pydantic `BaseSettings` |
| Testing | `pytest` |
| Linting | `ruff`, `mypy` |
| Packaging | `pyproject.toml` / `uv` |
| CI | GitHub Actions |

---

## Intended Directory Structure

This repo extends the upstream KDB-X MCP Server with custom `xqa_*` tools, resources, and prompts:

```
Agentic-DQ-for-KDB/
├── CLAUDE.md                        # This file
├── README.md                        # User-facing overview
├── LICENSE                          # Apache 2.0
├── pyproject.toml                   # Python project config & dependencies
├── .env.example                     # Template for required env vars (never commit .env)
├── .env                             # Local config (gitignored)
├── .gitignore
│
├── src/
│   └── mcp_server/                  # Extends upstream KDB-X MCP Server layout
│       ├── main.py                  # Server entry point
│       ├── settings.py              # Pydantic config schema
│       ├── tools/                   # Auto-discovered MCP tools
│       │   ├── _template.py         # Copy this to create a new tool
│       │   ├── xqa_get_venue_syms.py
│       │   ├── xqa_get_index_syms.py
│       │   ├── xqa_get_venue_hours.py
│       │   ├── xqa_align_trade_quote.py
│       │   └── xqa_get_condition_codes.py
│       ├── resources/               # Auto-discovered MCP resources
│       │   ├── _template.py
│       │   ├── xqa_trade_schema.py  # trade table schema description
│       │   ├── xqa_quote_schema.py  # quote table schema description
│       │   └── xqa_venue_guide.py   # venue / auction domain knowledge
│       ├── prompts/                 # Auto-discovered MCP prompts
│       │   ├── _template.py
│       │   └── xqa_dq_analysis.py   # DQ analysis prompt template
│       └── utils/
│           ├── db_connection.py     # get_db_connection() helper
│           └── embeddings.py        # Optional: vector search support
│
├── q/                               # Native KDB+/q scripts (loaded by tools)
│   ├── init.q                       # Startup / bootstrapping
│   ├── tools/
│   │   ├── venue.q                  # .xqa.getVenueSyms, .xqa.getVenueHours
│   │   ├── index.q                  # .xqa.getIndexSyms
│   │   └── alignment.q              # .xqa.alignTradeQuote (aj wrapper)
│   └── utils.q                      # Shared q utilities
│
├── config/
│   ├── venues.yaml                  # Venue trading hours & timezone offsets
│   ├── indices.yaml                 # Index constituent definitions
│   └── connections.yaml             # KDB+ connection profiles (no credentials)
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── test_tools.py
│   │   ├── test_dq_checks.py
│   │   └── test_kdb_query.py
│   └── integration/
│       └── test_pipeline.py         # Requires live KDB-X instance
│
└── .github/
    └── workflows/
        ├── ci.yml
        └── release.yml
```

---

## Setup & Running the MCP Server

### Prerequisites

1. KDB-X or KDB+ running on a host/port
2. `uv` installed: `pip install uv` or see [astral.sh/uv](https://docs.astral.sh/uv/)
3. Clone the upstream server and this repo side-by-side, or extend it in-place
4. Claude Desktop installed (or another MCP-compatible client)

### 1. Start KDB-X / KDB+

```bash
# Classic KDB+
q -p 5000
# then in q: \l s.k_

# KDB-X
q -p 5000
# then in q:
# .ai:use`kx.ai
# .s.init[]
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in values. **Never commit `.env`.**

```bash
# KDB-X database connection
KDBX_DB_HOST=127.0.0.1
KDBX_DB_PORT=5000
KDBX_DB_USERNAME=           # optional
KDBX_DB_PASSWORD=           # optional
KDBX_DB_TIMEOUT=1
KDBX_DB_RETRY=2
KDBX_DB_TLS=false

# MCP server
KDBX_MCP_TRANSPORT=streamable-http   # or stdio
KDBX_MCP_HOST=127.0.0.1
KDBX_MCP_PORT=8000
KDBX_MCP_LOG_LEVEL=INFO

# Optional: Anthropic (if calling the API directly from tools)
ANTHROPIC_API_KEY=sk-ant-...

# Optional: alerting
SLACK_WEBHOOK_URL=
```

Configuration priority: **CLI args > env vars > .env file > defaults**

### 3. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "kdbx": {
      "command": "uv",
      "args": [
        "run",
        "--with", "streamable-http==0.1.4",
        "--directory", "/path/to/Agentic-DQ-for-KDB",
        "mcp-server"
      ],
      "env": {
        "KDBX_DB_HOST": "127.0.0.1",
        "KDBX_DB_PORT": "5000",
        "KDBX_MCP_TRANSPORT": "streamable-http"
      }
    }
  }
}
```

### 4. Run the Server

```bash
# Defaults: streamable-http on 127.0.0.1:8000, connects to KDB+ on localhost:5000
uv run mcp-server

# Custom ports
uv run mcp-server --db.port 5001 --mcp.port 7001

# stdio transport (same-host only, used by some clients)
uv run mcp-server --mcp.transport stdio

# Debug logging
uv run mcp-server --mcp.log-level DEBUG
```

---

## Writing Custom MCP Tools

Every `.py` file placed in `src/mcp_server/tools/` is auto-discovered at startup. Each must expose `get_tool()` and `execute()`.

```python
# src/mcp_server/tools/xqa_get_venue_hours.py
from mcp.server.models import Tool
from src.mcp_server.utils.db_connection import get_db_connection
import logging

logger = logging.getLogger(__name__)

def get_tool() -> Tool:
    return Tool(
        name="xqa_get_venue_hours",
        description=(
            "Returns trading session hours, auction timings, and UTC offset "
            "for a given venue. Use this before any completeness or timestamp check "
            "to understand expected trading windows and convert to storage timezone."
        ),
        inputSchema={
            "type": "object",
            "properties": {
                "venue_code": {
                    "type": "string",
                    "description": "Exchange MIC code, e.g. XTKS for Tokyo Stock Exchange"
                }
            },
            "required": ["venue_code"]
        }
    )

async def execute(venue_code: str) -> dict:
    try:
        conn = get_db_connection()
        # q wrapper: returns session boundaries + UTC offset from venueMap
        result = conn.q(f'select from venueMap where venue=`{venue_code}')
        return {"status": "success", "data": result.pd().to_dict(orient="records")}
    except Exception as e:
        logger.error(f"xqa_get_venue_hours failed: {e}")
        return {"status": "error", "message": str(e)}
```

> **Tool naming:** All project-specific tools use the `xqa_` prefix. Built-in KX tools use `kdbx_`.

### Tool Design Principles

- Provide **general context**, not check-specific logic. The AI generates check logic dynamically.
- Return raw data the AI can reason about — don't pre-filter to "interesting" rows.
- Keep tool descriptions precise: the AI selects tools autonomously based on their `description` field.
- q wrappers outperform SQL for large tick tables — use `conn.q(...)` not `kdbx_run_sql_query`.

```python
# Good: general-purpose, reusable
Tool(name="xqa_get_venue_hours", description="Returns session hours and UTC offset for a venue.")

# Avoid: too specific, not reusable
Tool(name="check_data_outside_trading_hours", ...)
```

---

## Writing Custom MCP Resources

Every `.py` file in `src/mcp_server/resources/` is auto-discovered. Each must expose `get_resource()` and `get_content()`.

```python
# src/mcp_server/resources/xqa_trade_schema.py
from mcp.server.models import Resource

def get_resource() -> Resource:
    return Resource(
        uri="kdbx://xqa-trade-schema",
        name="xqa_trade_schema",
        description="Schema and column definitions for the trade table",
        mimeType="text/markdown"
    )

async def get_content() -> str:
    return """
# trade table schema

| Column | Type    | Description |
|--------|---------|-------------|
| date   | date    | Partition date |
| sym    | symbol  | Instrument identifier (e.g. `7203.T`) |
| time   | time    | Event timestamp in storage timezone (JST −1h) |
| price  | float   | Trade price in local currency |
| size   | long    | Trade size in shares |
| code   | symbol  | Exchange condition code |
| flag   | symbol  | Auction flag: `opening`, `closing`, or null for continuous |

**Partitioning:** Table is date-partitioned. Always include `date` in WHERE clause.
**Timezone:** Data is stored as JST −1h (UTC+8). Tokyo open 09:00 JST = 08:00 in data.
**Sampling warning:** Do NOT sample this table. Use date + sym filters to scope queries.
"""
```

Resources act as the AI's internal documentation. Explicit schema resources prevent malformed queries on large partitioned tables.

---

## Writing Custom MCP Prompts

Every `.py` file in `src/mcp_server/prompts/` is auto-discovered. Each must expose `get_prompt()` and `get_content()`.

```python
# src/mcp_server/prompts/xqa_dq_analysis.py
from mcp.server.models import Prompt, PromptArgument

def get_prompt() -> Prompt:
    return Prompt(
        name="xqa_dq_analysis",
        description="Generate a scoped DQ analysis prompt for a specific date and index",
        arguments=[
            PromptArgument(name="date",  description="Analysis date (YYYY-MM-DD)", required=True),
            PromptArgument(name="index", description="Index name, e.g. TOPIX",      required=True),
            PromptArgument(name="venue", description="Venue MIC code, e.g. XTKS",   required=True),
        ]
    )

async def get_content(date: str, index: str, venue: str) -> str:
    return f"""
SCOPE:
- Time period: ONLY USE DATA FOR {date}. DO NOT LOOK AT ANY OTHER DATES.
- Symbols: use symbols from the {index} index (call xqa_get_index_syms)
- trade table schema: date, sym, time, price, size, code, flag
- quote table schema: date, sym, time, ask, asize, bid, bsize

Answer the following questions:
1. Are there any gaps in trade or quote data?
2. Is the data distributed correctly across the {venue} trading sessions?
3. Are there any null or negative values in price or size columns?
4. Are there any crossed quotes (bid >= ask) during continuous trading hours?
5. Are auction trades correctly flagged?
6. Are trade and quote timestamps correctly aligned?

Constraints:
- Ensure ALL data is used (no sampling)
- Always use date-partitioned queries (include `date={date}` in every query)
- Call xqa_get_venue_hours for {venue} before applying any time filters
- For gap detection: explicitly check 1-minute bins
- For each finding, state exactly which data was used and how many rows were analyzed
"""
```

---

## DQ Check Implementation Guide

### 1. Data Completeness

Checks whether data covers the expected trading sessions without gaps.

**Approach:**
- Call `xqa_get_venue_hours` to retrieve official trading hours and timezone offset
- Convert venue local time to storage timezone before comparing (e.g., JST −1h = UTC+8)
- Aggregate trade/quote counts by time period (pre-open, morning session, lunch, afternoon, post-close)
- Flag sessions with zero or anomalously low record counts

**Key lesson from whitepaper:** The AI correctly deduced timezone offset from config *without being prompted*, converting JST to storage timezone automatically. 99.93% of trades and 96.4% of quotes fell within official trading hours on clean data.

### 2. Timestamp Consistency

Checks for temporal gaps and event ordering within trading sessions.

**Approach:**
- Bin trade/quote records into 1-minute intervals
- Flag bins with zero records during expected continuous-trading windows
- Cross-reference gaps against auction schedule

**Key lessons from whitepaper:**
- Large gaps (30 min) are detected reliably by default
- Small gaps (≤3 min) require explicit instruction: *"Check 1-minute bins and flag any minute with zero trades during continuous trading hours"*
- The AI may misattribute gaps to auction periods even when auction config says otherwise — always require a cross-check against `xqa_get_venue_hours` timings

### 3. Data Validation

#### Bad Data (Nulls / Negatives)
- Check `price` and `size` columns for null values and negative entries
- Report count and percentage of affected records
- Reliable only when the AI is given the full dataset — explicitly prevent sampling

#### Crossed Quotes
- During continuous trading, `bid < ask` must always hold
- `bid >= ask` = crossed quote — indicates feed error or special market condition
- On TSE, crossed quotes during auction periods are expected (special quotation mechanism)
- Always filter to continuous trading hours using `xqa_get_venue_hours` session boundaries

#### Outliers
- Detect price deviations >N standard deviations from rolling average using q's `mavg`/`mdev`
- Provide context window (trades ±30 seconds around outlier) to confirm it is not a genuine market move
- Common causes: fat-finger input, data-feed glitch, decimal-point misplacement

#### Duplicates
- Reference tables (`stockCodes`, `venueMap`) must be checked for duplicates
- Not all duplicates are errors — the AI should apply domain reasoning:
  - `stockCodes`: Duplicate ISINs/names may be cross-listings, ETF families, or multi-venue stocks
  - `venueMap`: Duplicate venue codes with different effective dates = operating hours change (valid)
- Always confirm AI's reasoning with a domain expert; the AI has been observed to give plausible-but-wrong explanations

### 4. Data Understanding

#### Auction Classification
- Auction trades should be flagged in the `flag` column with values `"opening"` / `"closing"`
- Opening auction: concentrated execution at market open, ~1-second window, large average size
- Closing auction: similar characteristics at market close
- Verify: auction trade count matches expected symbol count; average size >> continuous session trades

#### Trade-Quote Alignment
- Use q's `aj` (asof join) via `xqa_align_trade_quote` to align each trade with its immediately preceding quote
- A correctly aligned trade has `trade_price == bid` or `trade_price == ask`
- Alignment degrades during high-volatility periods (market open/close) due to quote-to-trade ratio spikes
- Quote-to-trade ratios >50:1 indicate high latency risk zones — flag these periods

---

## Prompt Engineering for DQ Checks

### Effective Prompt Structure

```
SCOPE:
- Time period: ONLY USE DATA FOR [DATE], DO NOT LOOK AT ANY OTHER DATES
- Symbols: use symbols from the [INDEX] index
- trade table schema: date, sym, time, price, size, code, flag
- quote table schema: date, sym, time, ask, asize, bid, bsize

Answer the following questions:
[DQ question 1]
[DQ question 2]

Constraints:
- Ensure ALL data is used (no sampling)
- Always use date-partitioned queries
- For each finding, state exactly which data was used
```

### Prompt Engineering Rules

| Rule | Why it matters |
|---|---|
| Always specify exact date(s) | Prevents querying unbounded time ranges → timeouts |
| Always provide table schema | Prevents malformed queries against large partitioned tables |
| Explicitly ban sampling | AI defaults to sampling large datasets; must be overridden every time |
| Use index symbols, not all symbols | Focuses analysis on the most liquid, representative instruments |
| Add verification checkpoints | "State what data was used" forces the AI to confirm coverage |
| Request date-partitioned queries | Critical for KDB-X performance on HDB tables |
| Specify timezone in prompt | AI handles timezone math correctly when offset is explicit |
| For gap detection: specify 1-min bins | AI misses small gaps without explicit granularity instruction |

### Phased Analysis Strategy

For large historical datasets, use a 3-phase approach:

```
Phase 1 — Statistical Sample (1–2 weeks)
  • Top 100 symbols (or one index)
  • 5–10 representative dates
  • Full daily analysis with date partitioning
  • Achievable within current MCP constraints ✓

Phase 2 — Problem Period Deep-Dive
  • Focus on dates where Phase 1 found issues
  • Expand symbol coverage for those specific dates
  • Achievable with careful partitioning ✓

Phase 3 — Full Historical Scan
  • Requires distributed compute or pre-aggregated summary tables
  • Not achievable with standard MCP tool constraints ✗
```

---

## KDB+/q Conventions

### q over SQL

Custom MCP tools **must** use q, not SQL:
- SQL via `kdbx_run_sql_query` caps at 1000 rows and is slow on tick data
- q direct calls via `get_db_connection().q(...)` have no row cap and far better performance

```python
from src.mcp_server.utils.db_connection import get_db_connection

conn = get_db_connection()
result = conn.q('select count i by date from trade where date=2023.05.08')
```

### Key q Functions for DQ

| Function | Use case |
|---|---|
| `aj` (asof join) | Trade-quote alignment — join each trade to its immediately preceding quote |
| `wj` (window join) | Quote statistics within a time window around each trade |
| `select ... by` | Aggregations by symbol/time for session-level completeness checks |
| `differ` | Detect consecutive duplicate timestamps |
| `mavg`, `mdev` | Rolling statistics for outlier detection |
| `count where null` | Null completeness checks |

### q Namespace Conventions

- Namespace DQ functions under `.dq` (e.g., `.dq.checkNull`, `.dq.profileTable`)
- Namespace custom MCP tool functions under `.xqa` (e.g., `.xqa.getVenueHours`)
- Keep q scripts in `q/tools/` short; orchestration logic belongs in Python

### Timezone Handling

KDB-X stores tick data in a configured "storage timezone" that may differ from venue local time:
1. Read the timezone offset from `venueMap` via `xqa_get_venue_hours`
2. Convert venue local trading hours to storage timezone before applying time filters
3. Document the offset in resource files (e.g., "JST −1h = data stored in UTC+8")

### Query Safety

- Never interpolate user-supplied strings directly into q queries (injection risk)
- Validate symbol names against `xqa_get_venue_syms` before embedding in queries
- All tools should be read-only — never execute insert/upsert/delete unless explicitly designed for remediation

---

## Agent / LLM Conventions

### Model Selection

- Default to `claude-sonnet-4-6` for all DQ analysis tasks (Sonnet-class validated by ExeQution Analytics)
- Use `claude-opus-4-6` for complex multi-step reasoning or ambiguous data patterns
- Use `claude-haiku-4-5-20251001` only for high-volume, simple classification sub-tasks

### Known AI Limitations (from whitepaper experiments)

| Limitation | Mitigation |
|---|---|
| AI defaults to sampling large datasets | Explicitly instruct "use ALL data, no sampling" in every prompt |
| Small gaps (≤3 min) missed by default | Instruct "check 1-minute bins explicitly" |
| AI may misattribute gaps to auction periods | Require cross-check against `xqa_get_venue_hours` auction schedule |
| AI gives plausible-but-wrong duplicate explanations | Human domain review is mandatory — treat AI reasoning as a starting point |
| SQL timeouts on large tick tables | Use q-language tools exclusively for tick data |
| Context window limits scope | Use phased analysis strategy (Phase 1 → 2 → 3) |

### Agentic DQ Loop

```
1. User submits DQ prompt (SCOPE: date, symbols, schema, constraints)
         │
2. AI calls xqa_get_index_syms and xqa_get_venue_hours to establish context
         │
3. AI calls tools iteratively, building understanding of the data shape
         │
4. AI executes q-based analysis queries (partitioned, scoped, no sampling)
         │
5. AI produces structured DQ report:
         • Coverage summary (rows analyzed, symbol count, date range)
         • Findings per DQ category with severity (INFO / WARNING / CRITICAL)
         • Root cause assessment with domain reasoning
         • Recommended action
         │
6. Human domain expert reviews and validates AI's reasoning
         │
7. Confirmed issues escalate to alerting / remediation pipeline
```

---

## Development Workflow

### Branch Conventions

- `main` — stable, production-ready code
- `master` — legacy default (treat same as `main` until unified)
- `claude/<description>-<session-id>` — AI-assisted development branches
- `feature/<ticket-or-description>` — human feature branches
- `fix/<description>` — bug fix branches

Always develop on feature branches, never commit directly to `main`/`master`.

### Commit Messages

```
Add xqa_get_venue_hours MCP tool with timezone support

Wraps venueMap table query to return session boundaries and UTC offset.
Required by completeness and timestamp consistency DQ checks.
```

### Git Push Protocol

```bash
git push -u origin <branch-name>
```

- Branch names starting with `claude/` must end with the matching session ID
- Retry up to 4 times on network failure with exponential backoff (2s, 4s, 8s, 16s)

---

## Running Tests

```bash
pytest tests/unit/                    # fast, no KDB-X required
pytest tests/integration/ --kdb-live  # requires live KDB-X connection
```

## Linting and Type Checking

```bash
ruff check src/ tests/
ruff format src/ tests/
mypy src/
```

---

## Code Style

- **Python 3.11+** minimum; all new modules must have type annotations
- `ruff` for formatting and linting; `mypy` in strict mode for `src/`
- Custom exceptions in `exceptions.py`; never swallow exceptions silently
- Log at `DEBUG` for MCP tool calls, `INFO` for pipeline milestones, `WARNING`/`ERROR` for failures
- Never log credentials, API keys, or raw query results containing PII

---

## Testing Guidelines

- Unit tests must be fast and KDB-X-independent (mock `get_db_connection()`)
- Integration tests must be skipped by default unless `--kdb-live` flag is passed
- Aim for >80% coverage on `src/`
- Tests for MCP tools should verify q query correctness against fixture data
- Tests for DQ logic should inject known bad data (nulls, negatives, outliers) and assert correct detection

---

## Security Considerations

- API keys and credentials always loaded from environment variables, never hardcoded
- q queries constructed from external input must be validated before execution
- The MCP server connects to KDB-X in **read-only mode** unless explicitly configured otherwise
- MCP tool descriptions must not expose internal table structures or credentials
- Review any auto-remediation actions before enabling in production

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `Failed to import pykx` | Set `QLIC` env var to your KDB+ license directory |
| Connection timeout | Verify KDB+ is running: `q -p 5000` |
| SQL interface error (KDB-X) | Run `.s.init[]` inside the q process |
| Port in use | Change port: `uv run mcp-server --mcp.port 7001` |
| Tools not appearing in Claude | Restart Claude Desktop after adding new tool files |
| AI sampling despite instruction | Restate "no sampling, use ALL data" explicitly in the prompt |

---

## License

Apache License 2.0. See [LICENSE](./LICENSE) for details. All contributions must be compatible with this license.
