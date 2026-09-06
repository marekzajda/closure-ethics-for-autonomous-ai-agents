#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Omega Sentinel v0.2.0.

Stable read-only telemetry layer built on the hardened v0.1.1 observer.

v0.2 goals
----------
* prefer psutil for process observation so Windows CIM stalls are not on the
  normal path;
* keep the v0.1.1 layered fallback if psutil is unavailable;
* emit a 30 s local human-readable dashboard;
* emit a compact bridge.json payload suitable for a GitHub Actions heartbeat;
* preserve Closure-Ethics observe-only semantics: no process control, no
  scientific-file modification, no network access from the Sentinel itself.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import socket
import time
from typing import Any, Dict

import omega_sentinel as base

VERSION = "0.2.0"
SCHEMA = "omega-sentinel-latest-v0.2"


def atomic_text(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def atomic_json(path: Path, obj: Dict[str, Any]) -> None:
    atomic_text(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


class SentinelV02(base.Sentinel):
    def __init__(self, config_path: Path):
        super().__init__(config_path)
        self.dashboard_path = self.telemetry_dir / "dashboard.txt"
        self.bridge_path = self.telemetry_dir / "bridge.json"
        self.sample_seq = 0

    def sample(self) -> Dict[str, Any]:
        t0 = time.perf_counter()
        self.sample_seq += 1
        state = super().sample()
        state["schema"] = SCHEMA
        state["sentinel_version"] = VERSION
        state["sample_seq"] = self.sample_seq
        state["sentinel_pid"] = os.getpid()
        state["sample_latency_ms"] = round((time.perf_counter() - t0) * 1000.0, 2)
        state["bridge"] = {
            "mode": "local_payload_only",
            "network_access": False,
            "recommended_publish_interval_seconds": int(self.config.get("bridge_interval_seconds", 300)),
        }
        return state

    def _bridge_payload(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "schema": "omega-sentinel-bridge-v0.2",
            "timestamp_utc": state.get("timestamp_utc"),
            "machine": state.get("machine", socket.gethostname()),
            "status": state.get("status"),
            "telemetry_health": state.get("telemetry_health"),
            "sample_seq": state.get("sample_seq"),
            "out_prefix": state.get("out_prefix"),
            "active_count": state.get("active_count"),
            "active_python_processes": [
                {
                    "pid": p.get("pid"),
                    "out_prefix": p.get("out_prefix"),
                    "backend": p.get("observation_backend"),
                }
                for p in state.get("active_python_processes", [])
            ],
            "classification": state.get("classification"),
            "error_patterns": state.get("error_patterns", []),
            "gpu": state.get("gpu", {}),
            "process_backend": (state.get("process_observation") or {}).get("backend"),
            "process_degraded": bool((state.get("process_observation") or {}).get("degraded")),
            "sample_latency_ms": state.get("sample_latency_ms"),
            "closure": state.get("closure", {}),
        }

    def _dashboard(self, state: Dict[str, Any]) -> str:
        gpu = state.get("gpu") or {}
        proc = state.get("process_observation") or {}
        active = state.get("active_python_processes") or []
        pids = ",".join(str(p.get("pid")) for p in active) if active else "none"
        errors = ", ".join(state.get("error_patterns") or []) or "none"
        lines = [
            "OMEGA SENTINEL v0.2",
            f"time_utc: {state.get('timestamp_utc')}",
            f"status: {state.get('status')}",
            f"telemetry_health: {state.get('telemetry_health')}",
            f"sample_seq: {state.get('sample_seq')}",
            f"sample_latency_ms: {state.get('sample_latency_ms')}",
            f"process_backend: {proc.get('backend')}",
            f"process_degraded: {proc.get('degraded')}",
            f"active_count: {state.get('active_count')}",
            f"active_pids: {pids}",
            f"out_prefix: {state.get('out_prefix')}",
            f"classification: {state.get('classification')}",
            f"error_patterns: {errors}",
            f"gpu: {gpu.get('name')} util={gpu.get('utilization_pct')}% mem={gpu.get('memory_used_mib')}/{gpu.get('memory_total_mib')} MiB temp={gpu.get('temperature_c')}C",
            f"closure: mode={(state.get('closure') or {}).get('mode')} policy={(state.get('closure') or {}).get('policy_version')}",
            "bridge: local payload only; GitHub transport remains external to Sentinel",
            "",
        ]
        return "\n".join(lines)

    def persist(self, state: Dict[str, Any]) -> None:
        # Preserve the canonical v0.1.1 latest/events/audit path first.
        super().persist(state)

        # Additional v0.2 outputs remain inside the telemetry subtree and are
        # checked by the same executable Closure kernel before every write.
        for path in (self.dashboard_path, self.bridge_path):
            d = self.kernel.assert_allowed(
                "write_local_telemetry",
                path,
                risk={"irreversible": 0.0, "scientific": 0.0, "external": 0.0, "privilege": 0.0, "uncertainty": 0.0},
                require_telemetry_target=True,
            )
            self.audit(d)
        atomic_text(self.dashboard_path, self._dashboard(state))
        atomic_json(self.bridge_path, self._bridge_payload(state))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    return SentinelV02(Path(args.config)).run(once=args.once)


if __name__ == "__main__":
    raise SystemExit(main())
