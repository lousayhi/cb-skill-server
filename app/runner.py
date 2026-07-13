"""Sandboxed execution of script-type skills via Docker-in-Docker (one-shot container)."""
from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Any

import docker
from docker.errors import DockerException

from .config import get_settings
from .models import InvokeResult, SkillManifest

logger = logging.getLogger("skills.runner")

_RUNTIME_COMMANDS: dict[str, list[str]] = {
    "python3": ["python3"],
    "python": ["python3"],
    "bash": ["bash"],
    "sh": ["sh"],
}


def _client():
    return docker.from_env()


def validate_input(manifest: SkillManifest, input_data: dict[str, Any]) -> None:
    import jsonschema

    schema = manifest.args or {"type": "object", "properties": {}}
    jsonschema.validate(instance=input_data, schema=schema)


def _command_for(manifest: SkillManifest) -> list[str]:
    base = _RUNTIME_COMMANDS.get((manifest.runtime or "sh").lower())
    if not base:
        # unknown runtime: treat runtime as the command, entry as arg
        base = [manifest.runtime]
    entry = manifest.entry or "script/run"
    return base + [f"/skill/{entry.lstrip('/')}"]


def invoke(manifest: SkillManifest, input_data: dict[str, Any]) -> InvokeResult:
    """Run a script-type skill inside an isolated, resource-limited container."""
    settings = get_settings()
    if manifest.type.value != "script":
        raise ValueError(f"Skill '{manifest.name}' is not a script-type skill")
    if not manifest.runtime or not manifest.entry:
        raise ValueError(f"Skill '{manifest.name}' missing runtime/entry")

    validate_input(manifest, input_data)

    skill_path = manifest.path
    if not skill_path or not Path(skill_path).exists():
        raise FileNotFoundError(f"Skill directory not found: {skill_path}")

    image = settings.runner_default_image
    if manifest.runtime.startswith("bash") or manifest.runtime == "sh":
        image = "bash:latest"

    start = time.time()
    try:
        client = _client()
    except DockerException as e:
        logger.error("Docker unavailable: %s", e)
        raise RuntimeError("Sandbox (Docker) unavailable") from e

    container = None
    try:
        try:
            container = client.containers.create(
                image,
                command=_command_for(manifest),
                environment={"SKILL_INPUT": json.dumps(input_data, ensure_ascii=False)},
                working_dir="/skill",
                volumes={skill_path: {"bind": "/skill", "mode": "ro"}},
                network_mode=None if settings.runner_network else "none",
                mem_limit=settings.runner_memory,
                cpu_period=100000,
                cpu_quota=int(settings.runner_cpus * 100000),
                pids_limit=settings.runner_pids_limit,
                read_only=True,
                user="1000:1000",
                cap_drop=["ALL"],
                detach=True,
            )
            container.start()
        except DockerException as e:
            logger.error("Docker execution failed: %s", e)
            raise RuntimeError(f"Sandbox execution failed: {e}") from e

        timed_out = False
        result_holder: dict[str, Any] = {}

        def _wait():
            try:
                result_holder["status"] = container.wait(timeout=settings.runner_timeout)
            except Exception:  # noqa: BLE001
                result_holder["status"] = None

        t = threading.Thread(target=_wait, daemon=True)
        t.start()
        t.join(settings.runner_timeout + 1)
        if t.is_alive() or result_holder.get("status") is None:
            timed_out = True
            try:
                container.kill()
            except Exception:  # noqa: BLE001
                pass
            status_code = -1
        else:
            status_code = (result_holder["status"] or {}).get("StatusCode", -1)

        logs = container.logs(stdout=True, stderr=True)
        stdout = logs.decode("utf-8", "replace")
        # crude split: docker returns combined; acceptable for MVP
        stderr = ""
        if timed_out:
            stderr = "execution timed out"

        return InvokeResult(
            name=manifest.name,
            exit_code=status_code,
            stdout=stdout,
            stderr=stderr,
            timed_out=timed_out,
            duration_ms=int((time.time() - start) * 1000),
        )
    finally:
        if container is not None:
            try:
                container.remove(force=True)
            except Exception:  # noqa: BLE001
                pass
