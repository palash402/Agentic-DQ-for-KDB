# Agentic-DQ-for-KDB

An AI-agent-driven **Data Quality (DQ)** framework for **KDB+/q** databases, powered by Claude and the [KDB-X MCP Server](https://github.com/KxSystems/kdb-x-mcp-server).

Claude autonomously detects data completeness gaps, timestamp inconsistencies, bad data points, anomalies, duplicates, and trade-quote misalignment in high-frequency financial market data — via natural language prompts, with no pre-written q queries required.

Inspired by [ExeQution Analytics — Agentic Workflow for Data Quality](https://exequtionanalytics.com/wp-content/uploads/2026/01/Agentic-Workflow-for-Data-Quality.pdf).

---

## Architecture

```
Claude Desktop  (natural language prompts)
      │
      │  MCP (streamable-http, port 8000)
      ▼
MCP Server  (uv run mcp-server)
  ├── TOOLS      → src/mcp_server/tools/   (auto-discovered)
  ├── RESOURCES  → src/mcp_server/resources/
  └── PROMPTS    → src/mcp_server/prompts/
      │
      │  q IPC (pykx, port 5000)
      ▼
KDB-X / KDB+
  └── trade, quote, stockCodes, venueMap tables
```

---

## DQ Check Categories

| Category | What it checks |
|---|---|
| **Completeness** | Gaps in data, distribution across trading sessions vs venue hours |
| **Timestamp Consistency** | Temporal gaps at 1-min granularity, event ordering vs venue schedule |
| **Validation** | Null/negative values, crossed quotes (bid >= ask), price outliers, reference duplicates |
| **Understanding** | Auction trade classification, trade-quote alignment via `aj`, latency risk zones |

---

## Prerequisites

1. **KDB-X or KDB+** running on a host/port (default: `localhost:5000`)
2. **`uv`** — `pip install uv` or see [astral.sh/uv](https://docs.astral.sh/uv/)
3. **Claude Desktop** — [claude.ai/download](https://claude.ai/download)
4. Python 3.11+

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/palash402/Agentic-DQ-for-KDB.git
cd Agentic-DQ-for-KDB
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env — set KDBX_DB_HOST, KDBX_DB_PORT to point at your KDB+ instance
```

### 3. Start KDB+

```bash
# Classic KDB+
q -p 5000

# KDB-X (additional init required)
q -p 5000
# then in the q session:
#   .ai:use`kx.ai
#   .s.init[]
#   \l q/init.q
```

### 4. Configure Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS)
or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "kdbx": {
      "command": "uv",
      "args": [
        "run",
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

### 5. Run the MCP server

```bash
uv run mcp-server
# Server starts on 127.0.0.1:8000
# Connects to KDB+ on localhost:5000
```

Restart Claude Desktop. The `kdbx` server will appear in the MCP panel.

---

## Custom Tools (`xqa_*`)

| Tool | Purpose |
|---|---|
| `xqa_get_venue_syms` | Returns all symbols traded on a given venue |
| `xqa_get_index_syms` | Returns index constituents (e.g. TOPIX top 50) |
| `xqa_get_venue_hours` | Returns venue trading hours + UTC offset |
| `xqa_align_trade_quote` | Trade-quote alignment via q's `aj` function |
| `xqa_get_condition_codes` | Exchange condition code definitions |

All tools are auto-discovered at startup — add a `.py` file to `src/mcp_server/tools/` and restart.

---

## Example Prompts

### Completeness check

```
Using xqa_get_index_syms for TOPIX and xqa_get_venue_hours for XTKS,
check whether trade data for 2024-05-08 covers all expected trading sessions.
Use ALL data, no sampling. Include date=2024.05.08 in every query.
```

### Timestamp consistency

```
For trade data on 2024-05-08 for TOPIX symbols on XTKS:
bin records into 1-minute intervals and flag any minute with zero trades
during continuous trading hours. Cross-check gaps against the auction schedule
from xqa_get_venue_hours.
```

### Data validation

```
For quote data on 2024-05-08:
1. Count null and negative values in bid, ask, bsize, asize.
2. Find crossed quotes (bid >= ask) during continuous trading hours only.
3. Report counts and percentages — use ALL rows, no sampling.
```

### Data understanding

```
For trade data on 2024-05-08, TOPIX symbols:
1. Verify auction trades are flagged as 'opening' or 'closing' in the flag column.
2. Use xqa_align_trade_quote to compute trade-quote alignment.
3. Identify quote-to-trade ratio by 30-minute window and flag any ratio > 50:1.
```

### Full DQ analysis (via prompt template)

In Claude Desktop, select the **`xqa_dq_analysis`** prompt and fill in:
- `date`: `2024-05-08`
- `index`: `TOPIX`
- `venue`: `XTKS`

---

## Project Structure

```
Agentic-DQ-for-KDB/
├── src/mcp_server/
│   ├── main.py            # Server entry point + auto-discovery
│   ├── settings.py        # Pydantic config (KDBX_* env vars)
│   ├── tools/             # xqa_* MCP tools
│   ├── resources/         # Schema docs and domain knowledge
│   ├── prompts/           # DQ prompt templates
│   └── utils/kdbx.py      # get_kdb_connection() helper
├── q/                     # Native q scripts loaded by tools
├── config/                # venues.yaml, indices.yaml
├── tests/                 # Unit + integration tests
└── .github/workflows/     # CI pipeline
```

---

## Running Tests

```bash
# Unit tests (no KDB+ required)
uv run pytest tests/unit/

# With coverage
uv run pytest tests/unit/ --cov=mcp_server --cov-report=term-missing

# Integration tests (requires live KDB+)
uv run pytest tests/integration/ -m kdb_live
```

## Linting & Type Checking

```bash
uv run ruff check src/ tests/
uv run mypy src/
```

---

## Adding a New Tool

1. Copy `src/mcp_server/tools/_template.py` to `src/mcp_server/tools/xqa_my_tool.py`
2. Implement `async def xqa_my_tool_impl(...)` with your q query
3. Register via `register_tools(mcp_server)` / `@mcp_server.tool()` decorator
4. Restart Claude Desktop — the tool auto-discovers on startup

See [CLAUDE.md](./CLAUDE.md) for full conventions and prompt engineering rules.

---

## References

- [Agentic Workflow for Data Quality — ExeQution Analytics](https://exequtionanalytics.com/wp-content/uploads/2026/01/Agentic-Workflow-for-Data-Quality.pdf)
- [KDB-X MCP Server (KxSystems)](https://github.com/KxSystems/kdb-x-mcp-server)
- [KDB-X MCP Server Docs](https://code.kx.com/kdb-x/integrations/mcp-server.html)

---

## License

Apache License 2.0 — see [LICENSE](./LICENSE).
