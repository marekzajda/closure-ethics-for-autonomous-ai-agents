#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Omega Sentinel v0.1.2 - read-only local telemetry agent.

Purpose
-------
Observe Omega Python research runs on the Windows workstation and write a small,
machine-readable local telemetry state. The agent does not start, stop, restart,
modify, delete, publish, or otherwise control scientific work.

v0.1.1 hardens Windows process observation. A slow/broken Win32_Process CIM
provider must never collapse the whole Sentinel into SENTINEL_ERROR. Process
observation therefore uses layered backends and reports degraded telemetry
explicitly while preserving Closure-Ethics observe-only semantics.

v0.1.2 prevents Windows from creating a visible console window for telemetry
subprocesses such as PowerShell and nvidia-smi when Sentinel runs via pythonw.

Every read/write operation is checked through the executable Closure Kernel.
The only autonomous writes are latest.json, events.ndjson, and closure_audit.ndjson
inside the dedicated _omega_sentinel subtree.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from closure_kernel import ClosureKernel, append_audit

VERSION = "0.1.2"
WINDOWS_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
ERROR_PATTERNS = [
    r"Traceback \(most recent call last\)",
    r"\bAttributeError\b",
    r"\bRuntimeError\b",
    r"\bMemoryError\b",
    r"CUDA out of memory",
    r"OutOfMemoryError",
    r"\bPicklingError\b",
    r"Process completed with exit code [1-9]",
    r"\bFAILED\b",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path: Path, obj: Dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def tail_text(path: Path, max_lines: int) -> List[str]:
    if not path.exists() or not path.is_file():
        return []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return [x.rstrip("\r\n") for x in lines[-max_lines:]]
    except OSError:
        return []


def parse_out_prefix(command_line: str) -> Optional[str]:
    if not command_line:
        return None
    m = re.search(r"(?:^|\s)--out\s+(?:\"([^\"]+)\"|'([^']+)'|([^\s]+))", command_line)
    if not m:
        return None
    return next((g for g in m.groups() if g), None)


def ps_json(command: str, timeout: int = 8) -> Any:
    script = (
        "[Console]::OutputEncoding=[System.Text.UTF8Encoding]::new();"
        "$ErrorActionPreference='Stop';" + command
    )
    p = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        creationflags=WINDOWS_NO_WINDOW,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.strip() or f"PowerShell exit {p.returncode}")
    raw = p.stdout.strip()
    return json.loads(raw) if raw else []


def _normalise_rows(data: Any) -> List[Dict[str, Any]]:
    if isinstance(data, dict):
        return [data]
    return [x for x in (data or []) if isinstance(x, dict)]


def process_table() -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Return python processes plus health metadata without making CIM fatal.

    Backend order:
      1) psutil, when available (fastest and independent of WMI/CIM)
      2) targeted Win32_Process CIM query with a short operation timeout
      3) Get-Process fallback (PID/name/start time only; no command line)

    The final fallback is intentionally degraded but usable. It excludes the
    Sentinel process itself and prevents a transient WMI stall from turning the
    whole telemetry agent into SENTINEL_ERROR.
    """
    errors: List[str] = []

    try:
        import psutil  # type: ignore
        rows: List[Dict[str, Any]] = []
        for proc in psutil.process_iter(["pid", "name", "cmdline", "create_time"]):
            try:
                info = proc.info
                name = str(info.get("name") or "")
                if name.casefold() not in {"python.exe", "pythonw.exe", "python", "pythonw"}:
                    continue
                pid = int(info.get("pid") or 0)
                if pid == os.getpid():
                    continue
                cmdline = info.get("cmdline") or []
                rows.append({
                    "ProcessId": pid,
                    "Name": name,
                    "CommandLine": subprocess.list2cmdline([str(x) for x in cmdline]) if cmdline else "",
                    "CreationDate": info.get("create_time"),
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return rows, {"ok": True, "backend": "psutil", "degraded": False, "errors": errors}
    except ModuleNotFoundError:
        errors.append("psutil:not_installed")
    except Exception as exc:
        errors.append(f"psutil:{type(exc).__name__}:{exc}")

    try:
        command = (
            "$x=Get-CimInstance Win32_Process "
            "-Filter \"Name='python.exe' OR Name='pythonw.exe'\" "
            "-OperationTimeoutSec 4 | "
            "Select-Object ProcessId,Name,CommandLine,CreationDate;"
            "$x | ConvertTo-Json -Compress -Depth 3"
        )
        rows = _normalise_rows(ps_json(command, timeout=7))
        rows = [r for r in rows if int(r.get("ProcessId") or 0) != os.getpid()]
        return rows, {"ok": True, "backend": "targeted_cim", "degraded": False, "errors": errors}
    except Exception as exc:
        errors.append(f"targeted_cim:{type(exc).__name__}:{exc}")

    try:
        command = (
            "$x=Get-Process -Name python,pythonw -ErrorAction SilentlyContinue | "
            "Select-Object Id,ProcessName,StartTime,Path;"
            "$x | ConvertTo-Json -Compress -Depth 3"
        )
        raw_rows = _normalise_rows(ps_json(command, timeout=5))
        rows = []
        for r in raw_rows:
            pid = int(r.get("Id") or 0)
            if pid == os.getpid():
                continue
            name = str(r.get("ProcessName") or "python")
            if not name.lower().endswith(".exe"):
                name += ".exe"
            rows.append({
                "ProcessId": pid,
                "Name": name,
                "CommandLine": "",
                "CreationDate": r.get("StartTime"),
                "Path": r.get("Path"),
            })
        return rows, {"ok": True, "backend": "get_process_fallback", "degraded": True, "errors": errors}
    except Exception as exc:
        errors.append(f"get_process:{type(exc).__name__}:{exc}")

    return [], {"ok": False, "backend": "unavailable", "degraded": True, "errors": errors}


def gpu_status() -> Dict[str, Any]:
    try:
        p = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            creationflags=WINDOWS_NO_WINDOW,
        )
        if p.returncode != 0 or not p.stdout.strip():
            return {"available": False, "error": p.stderr.strip()}
        row = [x.strip() for x in p.stdout.strip().splitlines()[0].split(",")]
        return {
            "available": True,
            "name": row[0],
            "utilization_pct": float(row[1]),
            "memory_used_mib": float(row[2]),
            "memory_total_mib": float(row[3]),
            "temperature_c": float(row[4]),
        }
    except Exception as exc:
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}


def latest_candidate(workspace: Path, pattern: str) -> Optional[Path]:
    items = []
    try:
        for p in workspace.glob(pattern):
            if p.is_file():
                try:
                    items.append((p.stat().st_mtime, p))
                except OSError:
                    pass
    except OSError:
        return None
    if not items:
        return None
    return max(items, key=lambda x: x[0])[1]


def load_summary(path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


class Sentinel:
    def __init__(self, config_path: Path):
        self.config_path = config_path.resolve()
        self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
        self.workspace = Path(self.config["workspace_root"]).resolve()
        self.telemetry_dir = Path(self.config["telemetry_dir"]).resolve()
        self.sample_seconds = int(self.config.get("sample_seconds", 30))
        self.heartbeat_seconds = int(self.config.get("heartbeat_seconds", 300))
        self.tail_lines = int(self.config.get("tail_lines", 40))
        self.command_patterns = [str(x).casefold() for x in self.config.get("command_patterns", ["omega_m5p4e"])]
        policy_path = Path(self.config.get("policy_path", self.config_path.with_name("closure_policy_v0_1.json"))).resolve()
        self.kernel = ClosureKernel(policy_path)
        self.telemetry_dir.mkdir(parents=True, exist_ok=True)
        self.latest_path = self.telemetry_dir / "latest.json"
        self.events_path = self.telemetry_dir / "events.ndjson"
        self.audit_path = self.telemetry_dir / "closure_audit.ndjson"
        self.last_status: Optional[str] = None
        self.last_heartbeat = 0.0
        self.process_health: Dict[str, Any] = {"ok": True, "backend": "not_sampled", "degraded": False, "errors": []}

    def audit(self, decision) -> None:
        write_decision = self.kernel.assert_allowed(
            "write_local_audit",
            self.audit_path,
            risk={"irreversible": 0.0, "scientific": 0.0, "external": 0.0, "privilege": 0.0, "uncertainty": 0.0},
            require_telemetry_target=True,
        )
        append_audit(self.audit_path, decision)
        append_audit(self.audit_path, write_decision)

    def allowed(self, action: str, target: Optional[Path] = None):
        d = self.kernel.evaluate(action, target)
        self.audit(d)
        if not d.allowed:
            raise PermissionError(f"Closure denied {action}: {d.reason}")
        return d

    def observe_processes(self) -> List[Dict[str, Any]]:
        self.allowed("read_process_table", self.workspace)
        rows, health = process_table()
        self.process_health = health
        out = []
        ws = str(self.workspace).casefold()
        commandline_available = not bool(health.get("degraded"))
        for r in rows:
            cmd = str(r.get("CommandLine") or "")
            low = cmd.casefold()
            relevant = (ws in low or any(pat in low for pat in self.command_patterns)) if commandline_available else True
            if not relevant:
                continue
            out.append({
                "pid": int(r.get("ProcessId") or 0),
                "name": r.get("Name"),
                "command_line": cmd or None,
                "creation_date": r.get("CreationDate"),
                "out_prefix": parse_out_prefix(cmd),
                "observation_backend": health.get("backend"),
                "commandline_available": bool(cmd),
            })
        return out

    def choose_logs(self, processes: List[Dict[str, Any]]) -> Tuple[Optional[Path], Optional[Path], Optional[str]]:
        prefix = None
        if processes:
            prefix = next((p.get("out_prefix") for p in processes if p.get("out_prefix")), None)
        if prefix:
            out = self.workspace / f"{prefix}_LIVE.stdout.log"
            err = self.workspace / f"{prefix}_LIVE.stderr.log"
            if out.exists() or err.exists():
                return (out if out.exists() else None, err if err.exists() else None, str(prefix))
        out = latest_candidate(self.workspace, "*_LIVE.stdout.log")
        err = latest_candidate(self.workspace, "*_LIVE.stderr.log")
        inferred = None
        if out:
            inferred = out.name[: -len("_LIVE.stdout.log")]
        elif err:
            inferred = err.name[: -len("_LIVE.stderr.log")]
        return out, err, inferred

    def sample(self) -> Dict[str, Any]:
        procs = self.observe_processes()

        self.allowed("read_gpu_status", self.workspace)
        gpu = gpu_status()

        stdout_path, stderr_path, prefix = self.choose_logs(procs)
        stdout_tail: List[str] = []
        stderr_tail: List[str] = []
        if stdout_path:
            self.allowed("read_log_tail", stdout_path)
            stdout_tail = tail_text(stdout_path, self.tail_lines)
        if stderr_path:
            self.allowed("read_log_tail", stderr_path)
            stderr_tail = tail_text(stderr_path, self.tail_lines)

        combined_err = "\n".join(stderr_tail[-self.tail_lines:])
        error_hits = [pat for pat in ERROR_PATTERNS if re.search(pat, combined_err, re.IGNORECASE)]

        summary_path = (self.workspace / f"{prefix}_summary.json") if prefix else None
        summary = None
        if summary_path and summary_path.exists():
            self.allowed("read_scientific_summary", summary_path)
            summary = load_summary(summary_path)

        process_ok = bool(self.process_health.get("ok"))
        if procs:
            status = "RUNNING"
        elif summary is not None:
            status = "COMPLETED"
        elif error_hits:
            status = "FAILED"
        elif not process_ok:
            status = "UNKNOWN"
        else:
            status = "IDLE"

        classification = summary.get("classification") if isinstance(summary, dict) else None
        state = {
            "schema": "omega-sentinel-latest-v0.1.2",
            "sentinel_version": VERSION,
            "timestamp_utc": utc_now(),
            "machine": socket.gethostname(),
            "status": status,
            "telemetry_health": "DEGRADED" if self.process_health.get("degraded") else ("OK" if process_ok else "ERROR"),
            "process_observation": self.process_health,
            "workspace_root": str(self.workspace),
            "active_python_processes": procs,
            "active_count": len(procs),
            "out_prefix": prefix,
            "stdout_log": str(stdout_path) if stdout_path else None,
            "stderr_log": str(stderr_path) if stderr_path else None,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "error_patterns": error_hits,
            "summary_path": str(summary_path) if summary_path and summary_path.exists() else None,
            "classification": classification,
            "gpu": gpu,
            "closure": {
                "mode": self.kernel.policy.get("mode"),
                "policy_version": self.kernel.policy.get("policy_version"),
                "policy_sha256": self.kernel.policy_sha256,
            },
        }
        return state

    def persist(self, state: Dict[str, Any]) -> None:
        d = self.kernel.assert_allowed(
            "write_local_telemetry",
            self.latest_path,
            risk={"irreversible": 0.0, "scientific": 0.0, "external": 0.0, "privilege": 0.0, "uncertainty": 0.0},
            require_telemetry_target=True,
        )
        self.audit(d)
        atomic_json(self.latest_path, state)

        now = time.monotonic()
        status_changed = state.get("status") != self.last_status
        heartbeat_due = (now - self.last_heartbeat) >= self.heartbeat_seconds
        if status_changed or heartbeat_due:
            event = {
                "timestamp_utc": state["timestamp_utc"],
                "status": state["status"],
                "telemetry_health": state.get("telemetry_health"),
                "process_backend": state.get("process_observation", {}).get("backend"),
                "active_count": state["active_count"],
                "out_prefix": state.get("out_prefix"),
                "classification": state.get("classification"),
                "error_patterns": state.get("error_patterns", []),
                "gpu": state.get("gpu", {}),
            }
            d2 = self.kernel.assert_allowed(
                "write_local_telemetry",
                self.events_path,
                risk={"irreversible": 0.0, "scientific": 0.0, "external": 0.0, "privilege": 0.0, "uncertainty": 0.0},
                require_telemetry_target=True,
            )
            self.audit(d2)
            with self.events_path.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n")
            self.last_heartbeat = now
            self.last_status = str(state.get("status"))

    def run(self, once: bool = False) -> int:
        while True:
            try:
                state = self.sample()
            except Exception as exc:
                state = {
                    "schema": "omega-sentinel-latest-v0.1.2",
                    "sentinel_version": VERSION,
                    "timestamp_utc": utc_now(),
                    "machine": socket.gethostname(),
                    "status": "SENTINEL_ERROR",
                    "telemetry_health": "ERROR",
                    "error": f"{type(exc).__name__}: {exc}",
                    "closure": {
                        "mode": self.kernel.policy.get("mode"),
                        "policy_version": self.kernel.policy.get("policy_version"),
                        "policy_sha256": self.kernel.policy_sha256,
                    },
                }
            self.persist(state)
            if once:
                print(json.dumps(state, indent=2, ensure_ascii=False))
                return 0
            time.sleep(self.sample_seconds)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    sentinel = Sentinel(Path(args.config))
    return sentinel.run(once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
