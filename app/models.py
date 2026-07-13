"""Pydantic models for skills."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class SkillType(str, Enum):
    content = "content"
    script = "script"


class SkillManifest(BaseModel):
    name: str
    version: str = "0.1.0"
    description: str = ""
    type: SkillType = SkillType.content
    runtime: str | None = None  # e.g. python3, bash — required when type==script
    entry: str | None = None    # script path/command — required when type==script
    args: dict[str, Any] | None = Field(default=None, description="JSON Schema for invoke input")
    tags: list[str] = Field(default_factory=list)

    # populated by registry, not from frontmatter
    path: str | None = None
    content_hash: str | None = None


class SkillSummary(BaseModel):
    name: str
    version: str
    description: str
    type: SkillType
    tags: list[str]


class InvokeRequest(BaseModel):
    input: dict[str, Any] = Field(default_factory=dict)


class InvokeResult(BaseModel):
    name: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False
    duration_ms: int = 0
