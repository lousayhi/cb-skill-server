# Skills 服务部署设计（Docker Compose + FastAPI）

- 日期：2026-07-13
- 目标：为项目组提供自托管的 skills 服务，同时托管 skills 文件并提供统一执行/代理入口，兼容 Cursor 与 CodeBuddy。

## 1. 整体架构与组件拓扑

一个 **FastAPI 服务** 身兼两职——既是 skills 仓库/分发中心，又是 MCP Server（统一执行入口）。docker-compose 编排如下：

```
┌─────────────┐   HTTPS + API Key   ┌────────────────────────────┐
│ Cursor /    │ ───────────────────▶│  Nginx (TLS 终止/反代)      │
│ CodeBuddy   │◀─────────────────── │                            │
└─────────────┘   MCP(SSE/Streamable)│  ┌──────────────────────┐  │
                       REST/调试     │  │  FastAPI skills-server│  │
                                     │  │  · 注册/检索/版本      │  │
                                     │  │  · MCP tools 暴露     │  │
                                     │  │  · 脚本沙箱执行        │  │
                                     │  └──────────┬───────────┘  │
                                     │   bind-mount│ git repo     │
                                     │  /data/skills (Git 仓库)   │
                                     └────────────────────────────┘
```

- **Nginx**：内网 HTTPS 终止、反向代理，可加 `auth_request` 校验 API Key。
- **FastAPI (skills-server)**：核心业务逻辑 + MCP 端点（`/mcp`，支持 Streamable HTTP 与 SSE）+ 镜像 REST（`/api/v1/...`）供调试/CI。
- **/data/skills**：宿主机 Git 仓库挂载进容器，skills 以目录形式存储（`SKILL.md` + 脚本 + 资源），用 Git 做版本与审计。

## 2. Skills 数据模型与注册流程

**Skill 目录结构**（每个 skill 一个目录，存于 Git 仓库）：

```
skills/
├── <skill-name>/
│   ├── SKILL.md          # frontmatter(YAML): name, version, description,
│   │                    #   type: content | script, runtime, entry, args
│   ├── script/          # type=script 时的执行脚本（仅可信 skill 有）
│   └── assets/          # 模板/文档/静态资源
```

**元数据来源**：`SKILL.md` 的 frontmatter 是唯一真相源。FastAPI 启动时（及 Git push/webhook 触发）扫描仓库，解析 frontmatter 生成内存索引（SQLite 缓存便于检索），不引入额外 DB 依赖，符合“文件系统 + Git”的取舍。

**注册/更新流程**：
1. 团队成员在本地写好 skill 目录 → `git push` 到 `/data/skills` 仓库（或提交 PR 由管理员合并，保证脚本类 skill 经 review）。
2. push 触发 webhook → 服务重建索引（解析 frontmatter、校验、计算 hash）。
3. 客户端通过 MCP `list_skills` 或 REST `GET /api/v1/skills` 即可看到新 skill。

- **content 型** skill：直接返回 SKILL.md 内容/模板给模型端执行。
- **script 型** skill：记录 `runtime`(python3/bash) + `entry` + 允许的参数 schema，供沙箱执行。

## 3. 执行沙箱与安全隔离

script 型 skill 会真正跑代码，是最大风险点。方案分两层：

**准入层（谁能被执行）**
- 只有经 Git PR review 合并的 script skill 才可执行；frontmatter 需显式声明 `type: script` 和 `runtime`。
- 服务加载时对每个 skill 计算内容 hash 并记录，执行时校验，防止运行期被篡改。

**执行层（怎么安全地跑）—— 推荐 Docker-in-Docker 一次性 runner 容器**
- skills-server 通过挂载的 `docker.sock` 为每次 script 调用启动一个隔离容器：
  - 只读挂载该 skill 目录，独立 `/tmp` 可写；
  - `--network none`（默认无网络，需网络的 skill 在 frontmatter 显式声明白名单）；
  - `--memory`、`--cpus`、`--pids-limit` 资源上限；
  - `--read-only` root fs、非 root 用户、`--cap-drop ALL`；
  - 硬超时（如 30s），超时强杀容器。
- 输入参数按 frontmatter 里的 args JSON Schema 校验后再传入，避免命令注入。
- 每次执行留审计日志（谁、哪个 skill、参数 hash、退出码、耗时）。

**权衡**：DinD 隔离性好但需挂 docker.sock（本身是特权）。轻量替代是同容器内 `subprocess + 资源限制`，实现简单但隔离弱。鉴于是公司内网、skill 经 review，建议起步用 DinD 一次性容器，安全与复杂度平衡最好。

## 4. MCP + REST 接口设计

**MCP 端点**（Cursor/CodeBuddy 直接连）：`/mcp`（Streamable HTTP）+ `/mcp/sse`（SSE 兼容），暴露 3 个工具：

- `list_skills(keyword?)` → 返回已注册 skill 列表（name/version/description/type）。
- `get_skill(name, version?)` → 返回 content 型 skill 的完整内容（提示词/模板），供模型端执行。
- `invoke_skill(name, input)` → 触发 script 型 skill：服务端沙箱执行，返回 stdout/结果。会先按 schema 校验 input。

每个工具带清晰 `description`，让模型知道何时调用。Cursor/CodeBuddy 配置只需填 MCP URL + API Key 即可。

**镜像 REST**（`/api/v1/...`，调试/CI 用）：
- `GET /skills` `GET /skills/{name}` `GET /skills/{name}/download`(tarball)
- `POST /skills/{name}/invoke` 同 invoke_skill
- `POST /webhook/git` Git push 触发索引重建（带 secret 校验）
- `GET /healthz` 健康检查（给 Nginx/compose 探活用）

所有接口走统一 **API Key 中间件**（Bearer / `X-API-Key`）。MCP 与 REST 共用同一套 service 层，避免逻辑分叉。

## 5. 部署（compose / Nginx / HTTPS）与测试

**docker-compose 组件**：
- `skills-server`：FastAPI 镜像（多段构建：python:3.12-slim + uv）。
- `nginx`：反向代理 + TLS，挂载自签/内网 CA 证书；`auth_request` 子请求校验 API Key。
- 挂载 `/data/skills`（Git 仓库，持久卷）+ `docker.sock`（DinD 执行）+ `nginx certs`。
- 可选 `watchtower` 做镜像自动更新（内网可选）。

**配置方式**：`.env` 注入 `API_KEYS`、`GIT_REPO_PATH`、`MCP_TOKEN`、`RUNNER_*`（内存/cpu/超时）。Nginx 用同一份 API Key 列表。

**HTTPS**：内网用自签证书或公司 CA；Nginx 终止 TLS，FastAPI 只听内网。对外暴露仅 443。

**Cursor/CodeBuddy 接入**（用户文档）：

```jsonc
// Cursor: .cursor/mcp.json
{ "mcpServers": { "team-skills": { "url": "https://skills.internal/mcp", "headers": { "Authorization": "Bearer <KEY>" } } } }
```

CodeBuddy 在设置里添加 MCP Server（URL + Header）同理。

**测试**：
- 单测：frontmatter 解析、schema 校验、索引构建。
- 集成：用 `fastapi.testclient` 跑 list/get/invoke 全流程；script skill 用无害 `echo` 验证沙箱（超时/无网络/资源限制）。
- CI：pytest + 构建镜像冒烟测试。

## 后续（实现阶段待确认）
- 是否启用 DinD 沙箱（vs 轻量 subprocess 起步）。
- Nginx `auth_request` 的具体校验实现（自研轻量校验服务 or 复用 FastAPI）。
- 是否接入公司 SSO/统一鉴权。
