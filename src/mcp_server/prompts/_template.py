"""Template for creating new xqa_* MCP prompts.

Prompts are parameterised prompt templates surfaced in Claude Desktop's
prompt picker. They are ideal for standardised, repeatable analyses
(e.g. run the same DQ checklist for any date / venue / index).

To add a new prompt:
1. Copy this file: cp _template.py xqa_my_prompt.py
2. Implement the _impl function to generate the prompt text
3. Update the decorator parameters and docstring

The server auto-discovers any .py file in this directory (except _ prefixed).
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


async def my_prompt_impl(subject: str, focus: str = "general") -> str:
    return f"""
SCOPE: Analyse {subject} with focus on {focus}.

[Add your prompt body here — constraints, questions, output format.]
"""


def register_prompts(mcp_server: Any) -> list[str]:
    """Called automatically by main.py at server startup."""

    @mcp_server.prompt()
    async def my_prompt(subject: str, focus: str = "general") -> str:
        """Brief description — shown in Claude Desktop prompt picker."""
        return await my_prompt_impl(subject, focus)

    return ["my_prompt"]
