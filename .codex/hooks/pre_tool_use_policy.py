#!/usr/bin/env python3
"""Thin Codex PreToolUse entry point for the Closure Ethics adapter."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import subprocess
import sys


def repo_root() -> Path:
    try:
        root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        if root:
            return Path(root).resolve()
    except (OSError, subprocess.CalledProcessError):
        pass
    return Path.cwd().resolve()


def load_gate(root: Path):
    path = root / "09-implementation" / "codex" / "closure_gate.py"
    spec = importlib.util.spec_from_file_location("closure_codex_gate", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Closure gate: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    gate = load_gate(repo_root())
    return int(gate.main(["hook"]))


if __name__ == "__main__":
    raise SystemExit(main())
