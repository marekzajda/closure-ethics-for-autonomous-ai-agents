"""Portable deterministic Closure Ethics pre-action classifier.

This is intentionally conservative and evidence-limited. It does not infer moral
truth or hidden intent. It classifies recognizable tool-call patterns into a
small set of Closure outcomes so the host can combine them with its own sandbox,
approval, authentication, and authorization controls.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Mapping, Sequence

PLUGIN_VERSION = "0.1.0"

REVIEW_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("merge_or_push", re.compile(r"(?i)\b(?:git\s+push|gh\s+pr\s+merge|git\s+merge)\b")),
    ("deployment", re.compile(r"(?i)\b(?:deploy|terraform\s+apply|kubectl\s+(?:apply|delete)|helm\s+(?:install|upgrade|uninstall))\b")),
    ("publication", re.compile(r"(?i)\b(?:publish|release|npm\s+publish|twine\s+upload)\b")),
    ("destructive", re.compile(r"(?i)(?:\brm\s+-rf\b|\bdel\s+/[sq]\b|\bRemove-Item\b.*\b-Recurse\b|\bdrop\s+(?:table|database)\b|\btruncate\s+table\b)")),
    ("privilege_change", re.compile(r"(?i)\b(?:sudo|runas|chmod\s+[047]*[467]|chown|setfacl|icacls)\b")),
    ("network_write", re.compile(r"(?i)(?:\bcurl\b[^\n]*(?:-X\s*(?:POST|PUT|PATCH|DELETE)|--data|--upload-file)|\bInvoke-(?:RestMethod|WebRequest)\b[^\n]*(?:-Method\s+(?:Post|Put|Patch|Delete)))")),
    ("remote_copy", re.compile(r"(?i)\b(?:scp|rsync\b[^\n]*\s[^\n]*:|sftp)\b")),
    ("persistence_change", re.compile(r"(?i)\b(?:crontab|schtasks\s+/create|systemctl\s+enable|launchctl\s+load|reg\s+add\b[^\n]*(?:\\Run|\\RunOnce))\b")),
    ("security_policy_change", re.compile(r"(?i)\b(?:ufw|firewall-cmd|netsh\s+advfirewall|secedit|auditpol)\b")),
)

# Hard denials are deliberately narrow. Users must remain able to disable or
# uninstall the plugin; the plugin must not create self-preserving persistence.
HARD_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "credential_exfiltration",
        re.compile(
            r"(?is)(?:id_rsa|id_ed25519|\.aws[/\\]credentials|\.npmrc|\.pypirc|OPENAI_API_KEY|AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN)"
            r".{0,240}(?:curl|Invoke-RestMethod|Invoke-WebRequest|nc\s|netcat|scp\s)"
        ),
    ),
    (
        "credential_exfiltration",
        re.compile(
            r"(?is)(?:curl|Invoke-RestMethod|Invoke-WebRequest|nc\s|netcat|scp\s)"
            r".{0,240}(?:id_rsa|id_ed25519|\.aws[/\\]credentials|OPENAI_API_KEY|AWS_SECRET_ACCESS_KEY|GITHUB_TOKEN)"
        ),
    ),
)

SENSITIVE_PATCH_MARKERS = (
    ".codex/",
    "agents.md",
    "hooks.json",
    "requirements.toml",
    ".github/workflows/",
    "plugin.json",
    "marketplace.json",
)

WRITE_VERBS = re.compile(r"(?i)(?:create|update|delete|send|publish|merge|deploy|write|execute|apply|remove|modify)")
SUBAGENT_VERBS = re.compile(r"(?i)(?:spawn|subagent|delegate|delegation)")
READ_VERBS = re.compile(r"(?i)(?:read|get|fetch|list|search|query|retrieve|inspect|view)")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _event_text(event: Mapping[str, Any]) -> str:
    try:
        return json.dumps(event.get("tool_input", {}), ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return str(event.get("tool_input", ""))


def _policy_fingerprint() -> str:
    payload = {
        "version": PLUGIN_VERSION,
        "review_patterns": [name for name, _ in REVIEW_PATTERNS],
        "hard_patterns": [name for name, _ in HARD_PATTERNS],
        "sensitive_patch_markers": SENSITIVE_PATCH_MARKERS,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


@dataclass(frozen=True)
class ClosureDecision:
    timestamp_utc: str
    status: str
    action: str
    reason_codes: tuple[str, ...]
    risk_flags: tuple[str, ...]
    policy_version: str = PLUGIN_VERSION
    policy_fingerprint: str = ""
    source: str = "omega-closure-plugin"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def classify_event(event: Mapping[str, Any]) -> ClosureDecision:
    """Classify one host PreToolUse event without executing the action."""
    tool_name = str(event.get("tool_name", "unknown"))
    text = _event_text(event)
    normalized = text.replace("\\\\", "/").lower()

    hard: list[str] = []
    review: list[str] = []

    for flag, pattern in HARD_PATTERNS:
        if pattern.search(text):
            hard.append(flag)

    if tool_name.lower() in {"bash", "shell", "local_shell", "powershell"}:
        for flag, pattern in REVIEW_PATTERNS:
            if pattern.search(text):
                review.append(flag)

    elif tool_name == "apply_patch":
        if "*** delete file:" in normalized:
            review.append("destructive")
        if any(marker in normalized for marker in SENSITIVE_PATCH_MARKERS):
            review.append("governance_or_security_change")

    elif tool_name.startswith("mcp__"):
        if WRITE_VERBS.search(tool_name):
            review.append("external_write")
        elif not READ_VERBS.search(tool_name):
            review.append("unknown_external_capability")

    elif SUBAGENT_VERBS.search(tool_name):
        review.append("delegation_or_capability_amplification")

    elif WRITE_VERBS.search(tool_name):
        # Unknown write-capable local functions deserve a scope check, while
        # ordinary reads remain quiet to avoid turning the plugin into noise.
        review.append("write_capability")

    hard_flags = _dedupe(hard)
    review_flags = _dedupe(review)
    fingerprint = _policy_fingerprint()

    if hard_flags:
        return ClosureDecision(
            timestamp_utc=_utc_now(),
            status="DENY",
            action=f"tool:{tool_name}",
            reason_codes=tuple(f"HARD_{x.upper()}" for x in hard_flags),
            risk_flags=_dedupe(hard_flags + review_flags),
            policy_fingerprint=fingerprint,
        )

    if review_flags:
        return ClosureDecision(
            timestamp_utc=_utc_now(),
            status="REQUIRE_HUMAN_REVIEW",
            action=f"tool:{tool_name}",
            reason_codes=("CONSEQUENTIAL_ACTION_REQUIRES_SCOPE_REPAIRABILITY_AND_AUTHORIZATION_CHECK",),
            risk_flags=review_flags,
            policy_fingerprint=fingerprint,
        )

    return ClosureDecision(
        timestamp_utc=_utc_now(),
        status="ALLOW",
        action=f"tool:{tool_name}",
        reason_codes=("NO_RECOGNIZED_CONSEQUENTIAL_PATTERN",),
        risk_flags=(),
        policy_fingerprint=fingerprint,
    )


def model_context(decision: ClosureDecision) -> str:
    if decision.status == "DENY":
        return (
            "Omega Closure Ethics blocked a narrow hard-invariant pattern: "
            + ", ".join(decision.risk_flags)
            + ". Do not evade the block by changing syntax. Use an authorized, non-exfiltrating alternative."
        )
    if decision.status == "REQUIRE_HUMAN_REVIEW":
        return (
            "Omega Closure Ethics classified this tool call as consequential ("
            + ", ".join(decision.risk_flags)
            + "). Before the side effect, verify explicit user authorization and scope, auditability, bounded repair/reversal, "
              "affected-party agency, and uncertainty. If those cannot be established from available evidence, stop and obtain review."
        )
    return ""
