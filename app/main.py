"""FastAPI application: REST API + mounted MCP server + auth + webhook."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from . import registry
from .api import router as api_router
from .auth import APIKeyMiddleware
from .config import get_settings
from .mcp_server import mcp

logging.basicConfig(level=get_settings().log_level)
logger = logging.getLogger("skills.server")

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry.rebuild()
    yield


app = FastAPI(title="Team Skills Server", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(APIKeyMiddleware)

app.include_router(api_router)

# MCP endpoints: Streamable HTTP (primary) + SSE (legacy compat).
app.mount("/mcp", mcp.streamable_http_app())
app.mount("/mcp/sse", mcp.sse_app())


@app.get("/healthz")
def healthz():
    return {"status": "ok", "skills": len(registry.list_skills())}


@app.post("/webhook/git")
async def git_webhook(request: Request, x_webhook_secret: str | None = Header(None, alias="X-Webhook-Secret")):
    if not x_webhook_secret or x_webhook_secret != settings.webhook_secret:
        raise HTTPException(status_code=401, detail="invalid webhook secret")
    rebuilt = registry.rebuild()
    return {"rebuilt": rebuilt, "skills": rebuilt}
