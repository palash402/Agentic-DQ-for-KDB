"""Template for creating new xqa_* MCP resources.

Resources are static or semi-static text/markdown that Claude reads for context
(schemas, domain guides, conventions). They are cheaper than tool calls and
should be used for anything that doesn't require a live DB query.

To add a new resource:
1. Copy this file: cp _template.py xqa_my_resource.py
2. Implement get_content_impl() returning markdown text
3. Update the URI and description

The server auto-discovers any .py file in this directory (except _ prefixed).
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def my_resource_impl() -> str:
    return """
# My Resource

Describe the content here in Markdown.
Claude will read this when it needs context about [topic].
"""


def register_resources(mcp_server: Any) -> list[str]:
    """Called automatically by main.py at server startup."""

    @mcp_server.resource("kdbx://my-resource")
    async def my_resource() -> str:
        """Brief description of what context this resource provides."""
        return await my_resource_impl()

    return ["my_resource"]
