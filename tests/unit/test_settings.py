"""Unit tests for settings module."""

import os
from unittest.mock import patch

import pytest

from mcp_server.settings import Settings, get_settings


def test_default_settings() -> None:
    s = Settings()
    assert s.db_host == "127.0.0.1"
    assert s.db_port == 5000
    assert s.mcp_port == 8000
    assert s.mcp_transport == "streamable-http"
    assert s.mcp_log_level == "INFO"


def test_env_override() -> None:
    with patch.dict(os.environ, {"KDBX_DB_PORT": "5001", "KDBX_MCP_PORT": "9000"}):
        s = Settings()
        assert s.db_port == 5001
        assert s.mcp_port == 9000


def test_get_settings_singleton() -> None:
    import mcp_server.settings as settings_mod
    settings_mod._settings = None  # reset singleton
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    settings_mod._settings = None  # clean up
