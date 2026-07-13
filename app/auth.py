"""API Key auth as a raw ASGI middleware (does not buffer responses, so MCP SSE streams)."""
from __future__ import annotations

from starlette.types import ASGIApp, Receive, Scope, Send

from .config import get_settings, api_key_set

PUBLIC_PATHS = {"/healthz"}


def _send_401(send: Send):
    async def _send():
        body = b'{"detail":"Invalid or missing API key."}'
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
                (b"www-authenticate", b"Bearer"),
            ],
        })
        await send({"type": "http.response.body", "body": body})

    return _send()


class APIKeyMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self.api_keys = api_key_set()

    def _extract_key(self, scope: Scope) -> str | None:
        auth = None
        xkey = None
        for k, v in scope.get("headers", []):
            if k == b"authorization":
                auth = v.decode("latin-1")
            elif k == b"x-api-key":
                xkey = v.decode("latin-1")
        if auth and auth.lower().startswith("bearer "):
            return auth[7:].strip()
        return xkey

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        # Docs paths are public for convenience; protect everything else.
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/openapi") or path.startswith("/redoc"):
            await self.app(scope, receive, send)
            return

        key = self._extract_key(scope)
        if key and key in self.api_keys:
            await self.app(scope, receive, send)
        else:
            await _send_401(send)
