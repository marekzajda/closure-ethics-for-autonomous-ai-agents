#!/usr/bin/env python3
"""Codex/ChatGPT PreToolUse entry point for Omega Closure Ethics."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys

PLUGIN_ROOT = Path(os.environ.get("PLUGIN_ROOT", Path(__file__).resolve().parents[1])).resolve()
SCRIPTS = PLUGIN_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from closure_gate import classify_event, model_context  # noqa: E402
from omega_sentinel_audit import append_receipt  # noqa: E402


def _read_event() -> dict:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _audit(decision) -> None:
    # Privacy by design: log only the decision envelope, never raw tool arguments.
    if decision.status == "ALLOW":
        return
    data_root = os.environ.get("PLUGIN_DATA")
    if not data_root:
        return
    append_receipt(data_root, decision.to_dict())


def main() -> int:
    event = _read_event()
    decision = classify_event(event)
    try:
        _audit(decision)
    except Exception:
        # The plugin remains defense-in-depth, not an OS security boundary. An
        # audit backend failure must not silently convert a denial into allow.
        if decision.status == "DENY":
            pass

    context = model_context(decision)
    if decision.status == "DENY":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": context,
            },
            "systemMessage": context,
        }
    elif decision.status == "REQUIRE_HUMAN_REVIEW":
        # Current PreToolUse has no independent 'ask' decision. We therefore
        # inject review context and leave actual approval to the host's native
        # permission/sandbox layer.
        output = {"systemMessage": context}
    else:
        output = {}

    sys.stdout.write(json.dumps(output, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
