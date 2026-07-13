"""Skills registry: scans the Git repo, parses SKILL.md frontmatter, builds index."""
from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict

import frontmatter
from pydantic import ValidationError

from .config import get_settings
from .models import SkillManifest, SkillSummary, SkillType

logger = logging.getLogger("skills.registry")

_registry: Dict[str, SkillManifest] = {}
_mtime: float = 0.0


def _hash_skill_dir(d: Path) -> str:
    h = hashlib.sha256()
    for root, _, files in os.walk(d):
        for f in sorted(files):
            p = Path(root) / f
            h.update(str(p).encode())
            h.update(p.read_bytes())
    return h.hexdigest()


def _parse_manifest(d: Path) -> SkillManifest | None:
    skill_md = d / "SKILL.md"
    if not skill_md.exists():
        return None
    try:
        post = frontmatter.load(skill_md)
    except Exception as e:  # noqa: BLE001
        logger.warning("Failed to parse %s: %s", skill_md, e)
        return None

    meta = dict(post.metadata)
    meta["name"] = meta.get("name") or d.name
    meta["path"] = str(d)
    meta["content_hash"] = _hash_skill_dir(d)
    try:
        return SkillManifest(**meta)
    except ValidationError as e:
        logger.warning("Invalid manifest in %s: %s", d, e)
        return None


def rebuild() -> int:
    """Rescan the skills directory and rebuild the in-memory index."""
    global _registry, _mtime
    settings = get_settings()
    base = Path(settings.skills_dir)
    if not base.exists():
        logger.error("Skills dir %s does not exist", base)
        _registry = {}
        return 0

    _mtime = base.stat().st_mtime
    new: Dict[str, SkillManifest] = {}
    for entry in sorted(base.iterdir()):
        if not entry.is_dir():
            continue
        if entry.name.startswith("."):
            continue
        manifest = _parse_manifest(entry)
        if manifest:
            new[manifest.name] = manifest
    _registry = new
    logger.info("Registry rebuilt: %d skills", len(_registry))
    return len(_registry)


def ensure_fresh() -> None:
    """Rebuild if the underlying directory has changed (cheap mtime check)."""
    global _mtime
    settings = get_settings()
    base = Path(settings.skills_dir)
    if base.exists() and base.stat().st_mtime > _mtime:
        rebuild()


def list_skills(keyword: str | None = None) -> list[SkillSummary]:
    ensure_fresh()
    out = []
    kw = (keyword or "").lower()
    for m in _registry.values():
        if kw and kw not in (m.name + m.description + " ".join(m.tags)).lower():
            continue
        out.append(SkillSummary(
            name=m.name, version=m.version, description=m.description,
            type=m.type, tags=m.tags,
        ))
    return out


def get_manifest(name: str) -> SkillManifest | None:
    ensure_fresh()
    return _registry.get(name)


def read_skill_content(name: str) -> str | None:
    """Return the raw SKILL.md body for content-type skills."""
    m = get_manifest(name)
    if not m or not m.path:
        return None
    skill_md = Path(m.path) / "SKILL.md"
    if not skill_md.exists():
        return None
    post = frontmatter.load(skill_md)
    return post.content


def skill_dir(name: str) -> Path | None:
    m = get_manifest(name)
    return Path(m.path) if m and m.path else None
