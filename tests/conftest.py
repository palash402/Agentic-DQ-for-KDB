"""Shared pytest fixtures for unit and integration tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest


# ---------------------------------------------------------------------------
# KDB+ connection mock
# ---------------------------------------------------------------------------

class MockKdbConnection:
    """Fake pykx.SyncQConnection that returns configurable results."""

    def __init__(self) -> None:
        self._responses: dict[str, object] = {}
        self.call_log: list[str] = []

    def set_response(self, pattern: str, value: object) -> None:
        """Register a response for queries containing *pattern*."""
        self._responses[pattern] = value

    def __call__(self, query: str, *args: object) -> MagicMock:
        self.call_log.append(query)
        for pattern, value in self._responses.items():
            if pattern in query:
                mock = MagicMock()
                if isinstance(value, pd.DataFrame):
                    mock.pd.return_value = value
                    mock.py.return_value = value.to_dict(orient="records")
                elif isinstance(value, list):
                    mock.py.return_value = value
                    mock.pd.return_value = pd.DataFrame({"sym": value})
                elif isinstance(value, dict):
                    mock.py.return_value = value
                else:
                    mock.py.return_value = value
                return mock
        # Default: return empty result
        mock = MagicMock()
        mock.py.return_value = []
        mock.pd.return_value = pd.DataFrame()
        return mock


@pytest.fixture
def mock_kdb() -> Generator[MockKdbConnection, None, None]:
    """Patch get_kdb_connection() with a MockKdbConnection instance."""
    conn = MockKdbConnection()
    with patch("mcp_server.utils.kdbx.get_kdb_connection", return_value=conn):
        # Also patch in each tool module (they import at call time so patching
        # the source module is sufficient, but we patch the utils module too)
        yield conn


# ---------------------------------------------------------------------------
# Sample data fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_venue_hours_df() -> pd.DataFrame:
    """Typical venueMap row for XTKS (storage timezone UTC+8)."""
    return pd.DataFrame([{
        "venue": "XTKS",
        "date": "2024.05.08",
        "tradingStart": "08:00:00",
        "tradingEnd": "14:00:00",
        "lunchStart": "10:30:00",
        "lunchEnd": "11:30:00",
        "utcOffset": 8,
    }])


@pytest.fixture
def sample_syms() -> list[str]:
    return ["7203.T", "6758.T", "8306.T", "9984.T", "6861.T"]


@pytest.fixture
def sample_trade_df(sample_syms: list[str]) -> pd.DataFrame:
    """1000-row trade DataFrame with known DQ issues injected."""
    import numpy as np

    rng = np.random.default_rng(42)
    n = 1000
    syms = rng.choice(sample_syms, size=n)
    prices = rng.uniform(1000, 5000, size=n).astype(float)
    sizes = rng.integers(100, 5000, size=n).astype(int)

    # Inject known issues
    prices[10] = -1.0           # negative price
    prices[20] = float("nan")   # null price
    sizes[30] = -100            # negative size
    sizes[40] = 0               # zero size
    prices[50] = 999_999.0      # extreme outlier (~200σ from rolling avg)

    return pd.DataFrame({
        "sym": syms,
        "price": prices,
        "size": sizes,
        "code": [""] * n,
        "flag": [None] * n,
    })


@pytest.fixture
def sample_quote_df(sample_syms: list[str]) -> pd.DataFrame:
    """Quote DataFrame with crossed quotes injected at known indices."""
    import numpy as np

    rng = np.random.default_rng(42)
    n = 5000
    syms = rng.choice(sample_syms, size=n)
    asks = rng.uniform(1001, 5001, size=n).astype(float)
    bids = asks - rng.uniform(0.1, 2.0, size=n)  # bid < ask (normal)

    # Inject crossed quotes at indices 100-102
    bids[100] = asks[100] + 1.0   # bid > ask
    bids[101] = asks[101]         # bid == ask (locked market)

    return pd.DataFrame({
        "sym": syms,
        "bid": bids,
        "ask": asks,
        "bsize": rng.integers(100, 10000, size=n),
        "asize": rng.integers(100, 10000, size=n),
    })


@pytest.fixture
def aligned_trade_quote_df(sample_syms: list[str]) -> pd.DataFrame:
    """Perfectly aligned trade-quote data (price always == bid or ask)."""
    import numpy as np

    rng = np.random.default_rng(42)
    n = 200
    asks = rng.uniform(1001, 5001, size=n).astype(float)
    bids = asks - rng.uniform(0.1, 2.0, size=n)
    # 50% of trades hit ask, 50% hit bid
    prices = [asks[i] if i % 2 == 0 else bids[i] for i in range(n)]

    return pd.DataFrame({
        "sym": rng.choice(sample_syms, size=n),
        "price": prices,
        "bid": bids,
        "ask": asks,
        "size": rng.integers(100, 1000, size=n),
    })
