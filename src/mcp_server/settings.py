from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="KDBX_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database connection
    db_host: str = "127.0.0.1"
    db_port: int = 5000
    db_username: str = ""
    db_password: str = ""
    db_timeout: int = 1
    db_retry: int = 2
    db_tls: bool = False

    # MCP server
    mcp_transport: Literal["streamable-http", "stdio"] = "streamable-http"
    mcp_host: str = "127.0.0.1"
    mcp_port: int = 8000
    mcp_log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    mcp_server_name: str = "Agentic-DQ-for-KDB"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
