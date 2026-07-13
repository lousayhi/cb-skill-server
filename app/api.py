"""REST API mirroring the MCP tools (debugging / CI use)."""
from __future__ import annotations

import io
import tarfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from . import registry
from .models import InvokeRequest, SkillType
from .runner import invoke as run_skill

router = APIRouter(prefix="/api/v1")


@router.get("/skills")
def get_skills(keyword: str | None = Query(None)):
    return registry.list_skills(keyword)


@router.get("/skills/{name}")
def get_skill(name: str):
    manifest = registry.get_manifest(name)
    if not manifest:
        raise HTTPException(status_code=404, detail="skill not found")
    return manifest.model_dump()


@router.get("/skills/{name}/content")
def get_skill_content(name: str):
    content = registry.read_skill_content(name)
    if content is None:
        raise HTTPException(status_code=404, detail="skill content not found")
    return {"name": name, "content": content}


@router.get("/skills/{name}/download")
def download_skill(name: str):
    d = registry.skill_dir(name)
    if not d:
        raise HTTPException(status_code=404, detail="skill not found")

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        tar.add(str(d), arcname=name)
    buf.seek(0)
    return StreamingResponse(
        buf,
        media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="{name}.tar.gz"'},
    )


@router.post("/skills/{name}/invoke")
def invoke_skill(name: str, req: InvokeRequest):
    manifest = registry.get_manifest(name)
    if not manifest:
        raise HTTPException(status_code=404, detail="skill not found")
    if manifest.type != SkillType.script:
        raise HTTPException(status_code=400, detail="skill is not script-type")
    try:
        result = run_skill(manifest, req.input)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return result.model_dump()



