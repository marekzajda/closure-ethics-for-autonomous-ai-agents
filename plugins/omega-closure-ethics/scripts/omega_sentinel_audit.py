"""Omega Sentinel-style local audit receipts for the portable plugin.

The adapter intentionally has a tiny authority surface: it may create the plugin
writable data directory and append only to closure_audit.ndjson inside it. It
never controls processes, edits project files, performs network I/O, or changes
privileges.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from typing import Any, Mapping

AUDIT_FILE = "closure_audit.ndjson"
MODE = "observe_only"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_bytes(obj: Mapping[str, Any]) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _last_hash(path: Path) -> str:
    if not path.exists() or path.stat().st_size == 0:
        return "0" * 64
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            pos = handle.tell() - 1
            while pos > 0:
                handle.seek(pos)
                if handle.read(1) == b"\n":
                    break
                pos -= 1
            if pos > 0:
                handle.seek(pos + 1)
            else:
                handle.seek(0)
            line = handle.readline().decode("utf-8").strip()
        if not line:
            return "0" * 64
        previous = json.loads(line)
        return str(previous.get("receipt_sha256", "0" * 64))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return "0" * 64


def append_receipt(data_root: str | Path, receipt: Mapping[str, Any]) -> Path:
    """Append one hash-chained receipt under PLUGIN_DATA and return its path."""
    root = Path(data_root).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    path = (root / AUDIT_FILE).resolve()
    if path.parent != root:
        raise PermissionError("Omega Sentinel audit target escaped PLUGIN_DATA")

    body = dict(receipt)
    body.setdefault("timestamp_utc", _utc_now())
    body["sentinel_mode"] = MODE
    body["previous_receipt_sha256"] = _last_hash(path)
    digest_input = dict(body)
    body["receipt_sha256"] = hashlib.sha256(_canonical_bytes(digest_input)).hexdigest()

    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        try:
            os.fsync(handle.fileno())
        except OSError:
            pass
    return path
