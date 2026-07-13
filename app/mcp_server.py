"""MCP server exposing skills as tools (mounted by main.py as /mcp and /mcp/sse)."""
from __future__ import annotations

import asyncio
from typing import Any

from mcp.server.fastmcp import FastMCP

from . import registry
from .models import SkillType
from .runner import invoke as run_skill

mcp = FastMCP("team-skills")


@mcp.tool()
async def list_skills(keyword: str | None = None) -> list[dict[str, Any]]:
    """List registered team skills. Optional keyword filters by name/description/tags."""
    return [s.model_dump() for s in registry.list_skills(keyword)]


@mcp.tool()
async def get_skill(name: str, version: str | None = None) -> str:
    """Return the full content (prompt/template) of a content-type skill by name."""
    content = registry.read_skill_content(name)
    if content is None:
        manifest = registry.get_manifest(name)
        if manifest is None:
            raise ValueError(f"Skill '{name}' not found")
        if manifest.type != SkillType.content:
            raise ValueError(f"Skill '{name}' is a script-type skill; use invoke_skill")
        raise ValueError(f"Skill '{name}' has no readable content")
    return content


@mcp.tool()
async def invoke_skill(name: str, input: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a script-type skill in the sandbox. Returns stdout/stderr/exit code."""
    manifest = registry.get_manifest(name)
    if manifest is None:
        raise ValueError(f"Skill '{name}' not found")
    if manifest.type != SkillType.script:
        raise ValueError(f"Skill '{name}' is not a script-type skill")
    result = await asyncio.to_thread(run_skill, manifest, input or {})
    return result.model_dump()
