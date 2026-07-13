# Team Skills Server

Self-hosted **skills registry + MCP server** for your project team, built with FastAPI and Docker Compose. It both **hosts skills** (as Git-versioned directories) and **serves them as MCP tools**, so Cursor and CodeBuddy can connect directly.

## Features

- **Skills as directories** under a Git repo (`SKILL.md` frontmatter = manifest).
- **Two skill types**: `content` (returns prompt/template to the model) and `script` (runs in a sandboxed one-shot Docker container).
- **MCP server** at `/mcp` (Streamable HTTP) and `/mcp/sse` (SSE) — both Cursor and CodeBuddy connect here.
- **Mirror REST API** at `/api/v1/...` for debugging and CI.
- **Git webhook** (`/webhook/git`) rebuilds the index on push.
- **API Key auth** (Bearer / `X-API-Key`), TLS terminated at Nginx.

## Quick start (local)

```bash
cp .env.example .env          # edit API_KEYS, WEBHOOK_SECRET
# generate self-signed certs (or drop your company certs in nginx/certs)
openssl req -x509 -newkey rsa:2048 -nodes -keyout nginx/certs/privkey.pem \
  -out nginx/certs/fullchain.pem -days 365 -subj "/CN=localhost"

docker compose up --build
```

The server is now at `https://localhost`. Health: `https://localhost/healthz`.

## Authoring a skill

Each skill is a directory under `skills/` with a `SKILL.md`:

```markdown
---
name: my-skill
version: 1.0.0
description: Short description shown to the model.
type: content          # or: script
tags: [utility]
# for script skills:
# runtime: python3
# entry: script/run.py
# args: {type: object, properties: {text: {type: string}}, required: [text]}
---

Your prompt / template content here.
```

- `content` skills return this body to the model.
- `script` skills run `entry` inside an isolated container; input JSON is passed via the `SKILL_INPUT` env var.

Push to the repo (or merge a PR) and the index updates automatically via webhook.

## Connecting clients

### CodeBuddy
Add an MCP Server with:
- **URL**: `https://<host>/mcp`
- **Headers**: `Authorization: Bearer <API_KEY>`

### Cursor (`.cursor/mcp.json`)
```json
{
  "mcpServers": {
    "team-skills": {
      "url": "https://<host>/mcp",
      "headers": { "Authorization": "Bearer <API_KEY>" }
    }
  }
}
```

Available MCP tools: `list_skills`, `get_skill`, `invoke_skill`.

## REST API (debug / CI)

| Method | Path | Description |
| ------ | ---- | ----------- |
| GET | `/api/v1/skills` | list skills (`?keyword=`) |
| GET | `/api/v1/skills/{name}` | skill manifest |
| GET | `/api/v1/skills/{name}/content` | raw SKILL.md body |
| GET | `/api/v1/skills/{name}/download` | tarball |
| POST | `/api/v1/skills/{name}/invoke` | run a script skill |
| POST | `/webhook/git` | rebuild index (`X-Webhook-Secret`) |
| GET | `/healthz` | health check |

## Security notes

- Script skills run in one-shot containers: read-only root fs, non-root user, `cap_drop ALL`, `--network none` by default, memory/CPU/PID limits, and a hard timeout.
- Only skills merged into the Git repo (reviewed) are executable.
- `docker.sock` is mounted read-only into the server for sandbox orchestration — restrict host access accordingly.

## Testing

```bash
pip install -e ".[dev]"
pytest
```
# cb-skill-server
