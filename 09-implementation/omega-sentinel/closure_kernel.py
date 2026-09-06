#!/usr/bin/env python
"""Minimal executable Closure Kernel for the Omega Sentinel case study.

This support module deliberately implements a narrow allow-list. It is not a
general safety oracle: it only constrains the Sentinel's own local observation
and telemetry I/O boundary.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Optional


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class Decision:
    timestamp_utc: str
    action: str
    target: Optional[str]
    allowed: bool
    reason: str
    mode: str
    policy_version: str
    risk: Dict[str, float]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def append_audit(path: Path, decision: Decision) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(decision.to_dict(), ensure_ascii=False, separators=(",", ":")) + "\n")


class ClosureKernel:
    """Fail-closed policy check for the Sentinel's explicitly declared I/O."""

    def __init__(self, policy_path: Path):
        self.policy_path = policy_path.resolve()
        raw = self.policy_path.read_bytes()
        self.policy_sha256 = hashlib.sha256(raw).hexdigest()
        self.policy = json.loads(raw.decode("utf-8"))
        self.mode = str(self.policy.get("mode", "observe_only"))
        self.policy_version = str(self.policy.get("policy_version", "unknown"))
        self.read_actions = set(self.policy.get("allowed_read_actions", []))
        self.write_actions = set(self.policy.get("allowed_write_actions", []))
        self.telemetry_dir_name = str(self.policy.get("telemetry_dir_name", "_omega_sentinel"))
        self.telemetry_files = set(self.policy.get("allowed_telemetry_files", []))
        self.risk_max = {str(k): float(v) for k, v in self.policy.get("max_autonomous_write_risk", {}).items()}

    def _is_telemetry_target(self, target: Optional[Path]) -> bool:
        if target is None:
            return False
        resolved = target.resolve()
        return self.telemetry_dir_name in resolved.parts and resolved.name in self.telemetry_files

    def evaluate(
        self,
        action: str,
        target: Optional[Path] = None,
        risk: Optional[Dict[str, float]] = None,
        require_telemetry_target: bool = False,
    ) -> Decision:
        supplied_risk = {str(k): float(v) for k, v in (risk or {}).items()}
        allowed = False
        reason = "action_not_allowlisted"

        if self.mode != "observe_only":
            reason = "policy_mode_is_not_observe_only"
        elif action in self.read_actions:
            allowed, reason = True, "allowlisted_read"
        elif action in self.write_actions:
            if require_telemetry_target and not self._is_telemetry_target(target):
                reason = "target_outside_dedicated_telemetry_files"
            elif any(supplied_risk.get(key, 0.0) > limit for key, limit in self.risk_max.items()):
                reason = "autonomous_write_risk_exceeds_policy"
            else:
                allowed, reason = True, "allowlisted_local_telemetry_write"

        return Decision(
            timestamp_utc=_utc_now(),
            action=action,
            target=str(target.resolve()) if target is not None else None,
            allowed=allowed,
            reason=reason,
            mode=self.mode,
            policy_version=self.policy_version,
            risk=supplied_risk,
        )

    def assert_allowed(
        self,
        action: str,
        target: Optional[Path] = None,
        risk: Optional[Dict[str, float]] = None,
        require_telemetry_target: bool = False,
    ) -> Decision:
        decision = self.evaluate(action, target, risk, require_telemetry_target)
        if not decision.allowed:
            raise PermissionError(f"Closure denied {action}: {decision.reason}")
        return decision
