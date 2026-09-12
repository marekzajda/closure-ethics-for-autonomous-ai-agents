#!/usr/bin/env python3
"""Repo-native Closure Ethics adapter for OpenAI Codex.

This module has two deliberately separate jobs:

1. ``evaluate`` consumes explicit, auditable evidence supplied by an adapter or
   human/operator and returns ALLOW / MODIFY / REQUIRE_HUMAN_REVIEW / DENY.
2. ``hook`` consumes a Codex PreToolUse event and applies only narrow,
   deterministic runtime checks that can be justified from the tool call itself.

It does not infer real-world consent, harm, identity, or authorization from raw
language.  Those facts require explicit evidence.  The runtime hook therefore
hard-blocks only recognizable guardrail/audit tampering and otherwise supplies
Closure context for consequential actions.

When an ``_omega_sentinel`` telemetry directory exists, decisions are appended
through Omega Sentinel's own observe-only ClosureKernel boundary.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Iterable, Mapping, Optional, Sequence

POLICY_VERSION = "closure-codex-v0.1"

# Governance choices for this reference adapter, not universal moral constants.
MIN_AUDITABILITY = 0.70
MIN_REPAIRABILITY = 0.50
MIN_REVERSIBILITY = 0.50
MAX_UNCERTAINTY_AUTONOMOUS = 0.35

HARD_DENY_FLAGS = frozenset(
    {
        "audit_tampering",
        "closure_guard_disable",
        "covert_persistence",
        "credential_exfiltration",
        "unauthorized_replication",
    }
)

CONSEQUENTIAL_FLAGS = frozenset(
    {
        "destructive",
        "external_write",
        "publication",
        "deployment",
        "merge_or_push",
        "privilege_change",
        "credential_use",
        "process_control",
        "policy_change",
        "persistence",
        "replication",
        "subagent_amplification",
        "scientific_output_write",
    }
)

PROTECTED_CONTROL_PATHS = (
    "agents.md",
    ".codex/hooks.json",
    ".codex/hooks/",
    ".agents/skills/closure-ethics/",
    "09-implementation/codex/",
    "09-implementation/omega-sentinel/closure_kernel.py",
    "09-implementation/omega-sentinel/closure_policy_v0_1.json",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clip01(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return min(1.0, max(0.0, number))


def _policy_fingerprint() -> str:
    raw = json.dumps(
        {
            "version": POLICY_VERSION,
            "min_auditability": MIN_AUDITABILITY,
            "min_repairability": MIN_REPAIRABILITY,
            "min_reversibility": MIN_REVERSIBILITY,
            "max_uncertainty_autonomous": MAX_UNCERTAINTY_AUTONOMOUS,
            "hard_deny_flags": sorted(HARD_DENY_FLAGS),
            "consequential_flags": sorted(CONSEQUENTIAL_FLAGS),
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True)
class GateDecision:
    timestamp_utc: str
    action: str
    target: Optional[str]
    status: str
    reason_codes: tuple[str, ...]
    risk_flags: tuple[str, ...]
    uncertainty: float
    policy_version: str = POLICY_VERSION
    policy_fingerprint: str = ""
    source: str = "codex-closure-gate"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["reason_codes"] = list(self.reason_codes)
        data["risk_flags"] = list(self.risk_flags)
        return data


def evaluate_manifest(manifest: Mapping[str, Any]) -> GateDecision:
    """Evaluate explicit Closure evidence.

    Expected evidence is intentionally compact.  Domain-specific systems may
    provide richer evidence, but should reduce it to these audited fields before
    calling the gate.
    """
    action = str(manifest.get("action", "unspecified"))
    target_raw = manifest.get("target")
    target = None if target_raw is None else str(target_raw)
    flags = tuple(sorted({str(x) for x in manifest.get("risk_flags", [])}))
    flag_set = set(flags)

    scope_authorized = bool(manifest.get("scope_authorized", False))
    explicit_authorization = bool(manifest.get("explicit_authorization", False))
    auditability = _clip01(manifest.get("auditability"), 0.0)
    repairability = _clip01(manifest.get("repairability"), 0.0)
    reversibility = _clip01(manifest.get("reversibility"), 0.0)
    uncertainty = _clip01(manifest.get("uncertainty"), 1.0)
    safer_alternative = bool(manifest.get("safer_alternative"))

    reasons: list[str] = []

    hard = sorted(flag_set & HARD_DENY_FLAGS)
    if hard:
        reasons.extend(f"HARD_INVARIANT_{x.upper()}" for x in hard)
        status = "DENY"
    else:
        consequential = bool(flag_set & CONSEQUENTIAL_FLAGS)
        weak_structure = (
            auditability < MIN_AUDITABILITY
            or repairability < MIN_REPAIRABILITY
            or reversibility < MIN_REVERSIBILITY
        )

        if consequential and weak_structure and safer_alternative:
            if auditability < MIN_AUDITABILITY:
                reasons.append("AUDITABILITY_BELOW_THRESHOLD")
            if repairability < MIN_REPAIRABILITY:
                reasons.append("REPAIRABILITY_BELOW_THRESHOLD")
            if reversibility < MIN_REVERSIBILITY:
                reasons.append("REVERSIBILITY_BELOW_THRESHOLD")
            reasons.append("USE_CLOSURE_PRESERVING_ALTERNATIVE")
            status = "MODIFY"
        elif consequential and not scope_authorized:
            reasons.append("ACTION_OUTSIDE_RESOLVED_SCOPE")
            status = "REQUIRE_HUMAN_REVIEW"
        elif consequential and not explicit_authorization:
            reasons.append("CONSEQUENTIAL_SIDE_EFFECT_NEEDS_EXPLICIT_AUTHORIZATION")
            status = "REQUIRE_HUMAN_REVIEW"
        elif consequential and uncertainty > MAX_UNCERTAINTY_AUTONOMOUS:
            reasons.append("MATERIAL_UNCERTAINTY_REQUIRES_REVIEW")
            status = "REQUIRE_HUMAN_REVIEW"
        elif consequential and weak_structure:
            if auditability < MIN_AUDITABILITY:
                reasons.append("AUDITABILITY_BELOW_THRESHOLD")
            if repairability < MIN_REPAIRABILITY:
                reasons.append("REPAIRABILITY_BELOW_THRESHOLD")
            if reversibility < MIN_REVERSIBILITY:
                reasons.append("REVERSIBILITY_BELOW_THRESHOLD")
            reasons.append("CONSEQUENTIAL_ACTION_LACKS_BOUNDED_RECOVERY_EVIDENCE")
            status = "REQUIRE_HUMAN_REVIEW"
        elif not consequential and not scope_authorized:
            reasons.append("ROUTINE_ACTION_SCOPE_NOT_ESTABLISHED")
            status = "REQUIRE_HUMAN_REVIEW"
        else:
            reasons.append("CLOSURE_CONSTRAINTS_SATISFIED")
            status = "ALLOW"

    return GateDecision(
        timestamp_utc=_utc_now(),
        action=action,
        target=target,
        status=status,
        reason_codes=tuple(reasons),
        risk_flags=flags,
        uncertainty=uncertainty,
        policy_fingerprint=_policy_fingerprint(),
    )


# ---------------------------- Codex hook classifier ----------------------------

_REVIEW_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("destructive", re.compile(r"(?i)(?:^|[;&|]\s*)(?:rm\s+-[^\n]*r|del\s+|erase\s+|remove-item\b[^\n]*-recurse|rmdir\s+/s|git\s+reset\s+--hard|git\s+clean\s+-[^\n]*f)")),
    ("merge_or_push", re.compile(r"(?i)\b(?:git\s+push|gh\s+pr\s+merge|git\s+merge\b)")),
    ("publication", re.compile(r"(?i)\b(?:gh\s+release\s+create|npm\s+publish|twine\s+upload|docker\s+push)\b")),
    ("deployment", re.compile(r"(?i)\b(?:kubectl\s+apply|terraform\s+apply|vercel\s+deploy|fly\s+deploy|gh\s+workflow\s+run)\b")),
    ("privilege_change", re.compile(r"(?i)\b(?:sudo|runas|chmod\s+[0-7]*[67][0-7]{2}|chown|setfacl)\b")),
    ("process_control", re.compile(r"(?i)\b(?:taskkill|stop-process|killall|pkill|shutdown|reboot)\b")),
    ("external_write", re.compile(r"(?i)\b(?:curl|wget|Invoke-RestMethod|Invoke-WebRequest)\b[^\n]*(?:-X\s*(?:POST|PUT|PATCH|DELETE)|--data|--form|-Method\s+(?:Post|Put|Patch|Delete))")),
    ("credential_use", re.compile(r"(?i)(?:\.ssh[/\\]|\.aws[/\\]credentials|\.env\b|gh\s+auth\s+token|credential|secret|api[_-]?key|access[_-]?token)")),
)

_HARD_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("audit_tampering", re.compile(r"(?i)(?:rm|del|erase|remove-item|truncate|clear-content|>\s*)[^\n]*closure_audit\.ndjson")),
    ("closure_guard_disable", re.compile(r"(?i)(?:hooks\s*=\s*false|codex_hooks\s*=\s*false|disable[^\n]*(?:closure|sentinel)|bypass[^\n]*(?:closure|sentinel))")),
    ("credential_exfiltration", re.compile(r"(?i)(?:curl|wget|invoke-restmethod|invoke-webrequest)[^\n]*(?:\.ssh|\.aws[/\\]credentials|\.env\b|api[_-]?key|access[_-]?token|secret)")),
)

_DESTRUCTIVE_CONTROL_RE = re.compile(
    r"(?is)(?:rm\s+|del\s+|erase\s+|remove-item\s+|rmdir\s+|\*\*\*\s+delete\s+file:).*?"
    + r"(?:agents\.md|\.codex[/\\]hooks|\.agents[/\\]skills[/\\]closure-ethics|09-implementation[/\\]codex|omega-sentinel[/\\]closure_(?:kernel|policy))"
)


def _flatten_tool_input(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return repr(value)


def classify_hook_event(event: Mapping[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Return ``(hard_flags, review_flags)`` based only on observable tool input."""
    tool_name = str(event.get("tool_name", ""))
    tool_input = event.get("tool_input", {})
    text = _flatten_tool_input(tool_input)
    normalized = text.replace("\\\\", "/").replace("\\", "/")

    hard: set[str] = set()
    review: set[str] = set()

    for flag, pattern in _HARD_PATTERNS:
        if pattern.search(text):
            hard.add(flag)
    if _DESTRUCTIVE_CONTROL_RE.search(normalized):
        hard.add("closure_guard_disable")

    if tool_name == "Bash":
        for flag, pattern in _REVIEW_PATTERNS:
            if pattern.search(text):
                review.add(flag)
    elif tool_name == "apply_patch":
        lower = normalized.lower()
        if "*** delete file:" in lower:
            review.add("destructive")
        if any(path in lower for path in PROTECTED_CONTROL_PATHS):
            review.add("policy_change")
    elif tool_name.startswith("mcp__"):
        # Tool names carry useful action semantics without pretending to infer
        # the real-world meaning of arbitrary arguments.
        if re.search(r"(?i)(?:create|update|delete|send|publish|merge|deploy|write|execute)", tool_name):
            review.add("external_write")
    elif re.search(r"(?i)(?:spawn|subagent|delegate)", tool_name):
        review.add("subagent_amplification")

    return tuple(sorted(hard)), tuple(sorted(review - hard))


def hook_decision(event: Mapping[str, Any]) -> tuple[dict[str, Any], GateDecision]:
    tool_name = str(event.get("tool_name", "unknown"))
    hard_flags, review_flags = classify_hook_event(event)
    all_flags = tuple(sorted(set(hard_flags) | set(review_flags)))

    if hard_flags:
        decision = GateDecision(
            timestamp_utc=_utc_now(),
            action=f"codex:{tool_name}",
            target=None,
            status="DENY",
            reason_codes=tuple(f"HARD_INVARIANT_{x.upper()}" for x in hard_flags),
            risk_flags=all_flags,
            uncertainty=0.0,
            policy_fingerprint=_policy_fingerprint(),
            source="codex-pretool-hook",
        )
        reason = (
            "Closure Ethics blocked a recognizable guardrail/audit violation: "
            + ", ".join(hard_flags)
            + ". Use a repair-preserving alternative; do not bypass by changing syntax."
        )
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            },
            "systemMessage": reason,
        }
        return output, decision

    if review_flags:
        decision = GateDecision(
            timestamp_utc=_utc_now(),
            action=f"codex:{tool_name}",
            target=None,
            status="REQUIRE_HUMAN_REVIEW",
            reason_codes=("CONSEQUENTIAL_TOOL_CALL_REQUIRES_SCOPE_CHECK",),
            risk_flags=all_flags,
            uncertainty=0.5,
            policy_fingerprint=_policy_fingerprint(),
            source="codex-pretool-hook",
        )
        context = (
            "Closure Ethics classified this as consequential ("
            + ", ".join(review_flags)
            + "). Confirm that the concrete side effect is within the user's explicit scope, "
              "is auditable, and has a bounded repair/reversal path. If that cannot be established, "
              "stop before further consequential side effects and request the missing review."
        )
        # Current Codex PreToolUse does not support permissionDecision='ask'.
        # We therefore add model-visible context and let native Codex sandbox /
        # PermissionRequest handle approvals, while hard invariants above block.
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": context,
            },
            "systemMessage": "Closure Ethics review classification: " + ", ".join(review_flags),
        }
        return output, decision

    decision = GateDecision(
        timestamp_utc=_utc_now(),
        action=f"codex:{tool_name}",
        target=None,
        status="ALLOW",
        reason_codes=("NO_DETERMINISTIC_CLOSURE_VIOLATION_DETECTED",),
        risk_flags=(),
        uncertainty=0.0,
        policy_fingerprint=_policy_fingerprint(),
        source="codex-pretool-hook",
    )
    # Empty JSON is a valid non-blocking hook response.
    return {}, decision


# ---------------------------- Omega Sentinel audit -----------------------------


def _git_root(start: Optional[Path] = None) -> Path:
    cwd = str((start or Path.cwd()).resolve())
    try:
        out = subprocess.check_output(
            ["git", "-C", cwd, "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if out:
            return Path(out).resolve()
    except (OSError, subprocess.CalledProcessError):
        pass
    return (start or Path.cwd()).resolve()


def _load_sentinel_kernel(repo_root: Path):
    module_path = repo_root / "09-implementation" / "omega-sentinel" / "closure_kernel.py"
    spec = importlib.util.spec_from_file_location("omega_sentinel_closure_kernel", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Omega Sentinel ClosureKernel from {module_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def append_sentinel_audit(repo_root: Path, decision: GateDecision, *, create: bool = False) -> bool:
    """Append a Codex decision through Omega Sentinel's own allow-listed boundary.

    By default this is active only when ``_omega_sentinel`` already exists.  Set
    ``OMEGA_SENTINEL_AUDIT=1`` or pass ``create=True`` to create the telemetry
    subtree intentionally.
    """
    telemetry_dir = repo_root / "_omega_sentinel"
    if not telemetry_dir.exists() and not create and os.environ.get("OMEGA_SENTINEL_AUDIT") != "1":
        return False

    kernel_module = _load_sentinel_kernel(repo_root)
    policy = repo_root / "09-implementation" / "omega-sentinel" / "closure_policy_v0_1.json"
    audit_path = telemetry_dir / "closure_audit.ndjson"
    kernel = kernel_module.ClosureKernel(policy)
    sentinel_decision = kernel.assert_allowed(
        "write_local_audit",
        target=audit_path,
        risk={
            "irreversible": 0.0,
            "scientific": 0.0,
            "external": 0.0,
            "privilege": 0.0,
            "uncertainty": 0.0,
        },
        require_telemetry_target=True,
    )

    # Preserve the Sentinel's native audit event first, then add the richer
    # Codex receipt as a separate append-only record.
    kernel_module.append_audit(audit_path, sentinel_decision)
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "record_type": "codex_closure_decision",
        **decision.to_dict(),
    }
    with audit_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    return True


# ------------------------------------ CLI --------------------------------------


def _read_json_file(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError("manifest must contain a JSON object")
    return value


def _cmd_evaluate(args: argparse.Namespace) -> int:
    manifest = _read_json_file(Path(args.manifest))
    decision = evaluate_manifest(manifest)
    audited = False
    if args.audit:
        audited = append_sentinel_audit(_git_root(), decision, create=args.create_audit_dir)
    payload = decision.to_dict()
    payload["omega_sentinel_audited"] = audited
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return {"ALLOW": 0, "MODIFY": 10, "REQUIRE_HUMAN_REVIEW": 20, "DENY": 30}[decision.status]


def _cmd_hook(_args: argparse.Namespace) -> int:
    try:
        event_raw = sys.stdin.read()
        event = json.loads(event_raw or "{}")
        if not isinstance(event, Mapping):
            raise ValueError("hook input must be a JSON object")
        output, decision = hook_decision(event)
        try:
            append_sentinel_audit(_git_root(Path(str(event.get("cwd", Path.cwd())))), decision)
        except Exception as exc:  # Audit failure must be visible but should not fake a policy denial.
            output.setdefault("systemMessage", f"Closure audit degraded: {exc}")
        print(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
        return 0
    except Exception as exc:
        # Fail visibly.  Codex treats hook failures separately; do not fabricate
        # an authorization decision from malformed evidence.
        print(json.dumps({"systemMessage": f"Closure hook error: {exc}"}, ensure_ascii=False))
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Closure Ethics gate for Codex")
    sub = parser.add_subparsers(dest="command", required=True)

    ev = sub.add_parser("evaluate", help="evaluate an explicit action manifest")
    ev.add_argument("--manifest", required=True)
    ev.add_argument("--audit", action="store_true", help="append through Omega Sentinel if available")
    ev.add_argument("--create-audit-dir", action="store_true", help="intentionally create _omega_sentinel audit directory")
    ev.set_defaults(func=_cmd_evaluate)

    hook = sub.add_parser("hook", help="consume a Codex PreToolUse event on stdin")
    hook.set_defaults(func=_cmd_hook)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
