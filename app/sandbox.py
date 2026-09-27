"""Dispatch a browser action to an isolated process (local subprocess or Docker).

Docker mode gives real isolation: no host mounts, dropped caps, restricted egress
should be configured at run time (see sandbox/Dockerfile and README). Local mode is
the fast fallback for the demo.
"""
import json
import subprocess
from pathlib import Path

from .config import ROOT, SANDBOX_IMAGE, SANDBOX_MODE

PY = str(ROOT / ".venv" / "bin" / "python")


def _run(module: str, args: list[str], mount_shot: str | None = None) -> dict:
    if SANDBOX_MODE == "docker":
        cmd = ["docker", "run", "--rm", "--network", "bridge", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges"]
        if mount_shot:
            cmd += ["-v", f"{Path(mount_shot).parent}:/out"]
        cmd += [SANDBOX_IMAGE, "python", "-m", module, *args]
    else:
        cmd = [PY, "-m", module, *args]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=90, cwd=ROOT)
    if proc.returncode != 0:
        return {"error": f"sandbox exit {proc.returncode}: {proc.stderr[-500:]}"}
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {"error": f"bad sandbox output: {proc.stdout[-300:]} {proc.stderr[-300:]}"}


def visit(url: str, screenshot_path: str) -> dict:
    shot = "/out/" + Path(screenshot_path).name if SANDBOX_MODE == "docker" else screenshot_path
    return _run("sandbox.worker", [url, shot], mount_shot=screenshot_path)


def submit(url: str, plan: dict) -> dict:
    return _run("sandbox.submit", [url, json.dumps(plan)])
