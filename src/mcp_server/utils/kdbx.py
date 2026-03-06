import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

# Module-level connection singleton — recreated on first call or after failure.
_connection: Any = None


def get_kdb_connection() -> Any:
    """Return a live pykx.SyncQConnection, creating or re-connecting as needed.

    Retries up to settings.db_retry times with 1-second backoff between attempts.
    Raises RuntimeError if all attempts fail.
    """
    global _connection

    # Return cached connection if it looks healthy
    if _connection is not None:
        try:
            _connection("1+1")  # lightweight ping
            return _connection
        except Exception:
            logger.warning("Existing KDB+ connection appears broken — reconnecting")
            _connection = None

    from mcp_server.settings import get_settings

    settings = get_settings()

    last_exc: Exception | None = None
    for attempt in range(1, settings.db_retry + 2):  # +2: first attempt + retries
        try:
            import pykx as kx  # type: ignore[import-untyped]

            kwargs: dict[str, Any] = {
                "host": settings.db_host,
                "port": settings.db_port,
                "timeout": settings.db_timeout,
                "tls": settings.db_tls,
            }
            if settings.db_username:
                kwargs["username"] = settings.db_username
            if settings.db_password:
                kwargs["password"] = settings.db_password

            _connection = kx.SyncQConnection(**kwargs)
            logger.info(
                "Connected to KDB+ at %s:%d (attempt %d)",
                settings.db_host,
                settings.db_port,
                attempt,
            )
            return _connection
        except Exception as exc:
            last_exc = exc
            logger.warning(
                "KDB+ connection attempt %d/%d failed: %s",
                attempt,
                settings.db_retry + 1,
                exc,
            )
            if attempt <= settings.db_retry:
                time.sleep(1)

    raise RuntimeError(
        f"Failed to connect to KDB+ at {settings.db_host}:{settings.db_port} "
        f"after {settings.db_retry + 1} attempts: {last_exc}"
    )
