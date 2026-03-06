"""MCP server entry point.

Auto-discovers all tools, resources, and prompts from their respective
subdirectories. Each module must expose a ``register_tools``,
``register_resources``, or ``register_prompts`` function that accepts the
MCP server instance.
"""

import importlib
import logging
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Any

import mcp_server.tools as tools_pkg
import mcp_server.resources as resources_pkg
import mcp_server.prompts as prompts_pkg

logger = logging.getLogger(__name__)


def _discover_and_register(
    package: ModuleType,
    register_fn_name: str,
    mcp: Any,
) -> list[str]:
    """Import every non-template module in *package* and call register_fn_name(mcp)."""
    registered: list[str] = []
    pkg_path = Path(package.__file__).parent  # type: ignore[arg-type]

    for module_info in pkgutil.iter_modules([str(pkg_path)]):
        if module_info.name.startswith("_"):
            continue
        full_name = f"{package.__name__}.{module_info.name}"
        try:
            mod = importlib.import_module(full_name)
        except Exception:
            logger.exception("Failed to import module %s", full_name)
            continue

        register_fn = getattr(mod, register_fn_name, None)
        if register_fn is None:
            logger.warning("Module %s has no %s() — skipped", full_name, register_fn_name)
            continue

        try:
            names: list[str] = register_fn(mcp)
            registered.extend(names or [])
            logger.debug("Registered from %s: %s", module_info.name, names)
        except Exception:
            logger.exception("register call failed in %s", full_name)

    return registered


def main() -> None:
    import argparse
    import mcp

    from mcp_server.settings import get_settings

    # --- CLI args (override env/file) ---
    parser = argparse.ArgumentParser(description="Agentic-DQ-for-KDB MCP Server")
    parser.add_argument("--db.host", dest="db_host", default=None)
    parser.add_argument("--db.port", dest="db_port", type=int, default=None)
    parser.add_argument("--mcp.port", dest="mcp_port", type=int, default=None)
    parser.add_argument("--mcp.host", dest="mcp_host", default=None)
    parser.add_argument("--mcp.transport", dest="mcp_transport", default=None)
    parser.add_argument("--mcp.log-level", dest="mcp_log_level", default=None)
    args = parser.parse_args()

    settings = get_settings()

    # Apply CLI overrides
    if args.db_host:
        settings.db_host = args.db_host
    if args.db_port:
        settings.db_port = args.db_port
    if args.mcp_port:
        settings.mcp_port = args.mcp_port
    if args.mcp_host:
        settings.mcp_host = args.mcp_host
    if args.mcp_transport:
        settings.mcp_transport = args.mcp_transport  # type: ignore[assignment]
    if args.mcp_log_level:
        settings.mcp_log_level = args.mcp_log_level  # type: ignore[assignment]

    logging.basicConfig(
        level=getattr(logging, settings.mcp_log_level),
        format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    )

    server = mcp.server.fastmcp.FastMCP(settings.mcp_server_name)

    tools = _discover_and_register(tools_pkg, "register_tools", server)
    resources = _discover_and_register(resources_pkg, "register_resources", server)
    prompts = _discover_and_register(prompts_pkg, "register_prompts", server)

    logger.info(
        "Registered %d tool(s): %s", len(tools), tools or "(none)"
    )
    logger.info(
        "Registered %d resource(s): %s", len(resources), resources or "(none)"
    )
    logger.info(
        "Registered %d prompt(s): %s", len(prompts), prompts or "(none)"
    )

    if settings.mcp_transport == "stdio":
        server.run(transport="stdio")
    else:
        server.run(
            transport="streamable-http",
            host=settings.mcp_host,
            port=settings.mcp_port,
        )
