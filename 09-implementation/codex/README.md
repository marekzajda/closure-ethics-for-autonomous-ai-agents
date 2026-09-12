# Closure Ethics integration for OpenAI Codex

This directory is the repo-native adapter that connects **Closure Ethics** to the current Codex extension surfaces: `AGENTS.md`, Codex Skills, and lifecycle hooks.

## Architecture

```text
User task / resolved scope
        |
        v
Codex Actor / Planner
        |
        +---- repository instructions: AGENTS.md
        |
        +---- reusable workflow: $closure-ethics
        |        .agents/skills/closure-ethics/SKILL.md
        |
        v
PreToolUse hook
.codex/hooks.json
        |
        v
closure_gate.py
   |          |
   |          +--> narrow deterministic runtime classifier
   |                 hard invariant -> DENY
   |                 consequential -> review context
   |                 ordinary -> pass
   |
   +--> explicit evidence evaluator
              ALLOW / MODIFY / REQUIRE_HUMAN_REVIEW / DENY
        |
        v
Codex native sandbox / permission flow / executor
        |
        v
optional Omega Sentinel append-only audit
_omega_sentinel/closure_audit.ndjson
```

## Why the layers are separate

Closure Ethics distinguishes **semantic understanding**, **authorization**, **admissibility**, and **execution**. The integration mirrors that separation rather than asking one LLM prompt to be actor, judge, and executor simultaneously.

The runtime hook only blocks violations that can be recognized deterministically from the tool call itself, such as:

- erasing `closure_audit.ndjson`;
- disabling Codex hooks / Closure controls;
- destructive removal of core Closure policy artifacts;
- recognizable credential exfiltration through a network command.

Other consequential actions are classified and surfaced to Codex as review context. Current Codex `PreToolUse` does not support a custom `permissionDecision: "ask"`; therefore the integration deliberately preserves Codex's native sandbox and `PermissionRequest` approval system rather than inventing an unsafe pseudo-approval channel.

## Files

- `../../AGENTS.md` — repository-wide Codex operating instructions.
- `../../.agents/skills/closure-ethics/SKILL.md` — reusable Closure Ethics skill.
- `../../.codex/config.toml` — explicitly enables current Codex hooks.
- `../../.codex/hooks.json` — installs the `PreToolUse` hook on supported local tools.
- `../../.codex/hooks/pre_tool_use_policy.py` — stable hook entry point.
- `closure_gate.py` — executable evaluator, hook classifier, and Omega Sentinel audit adapter.
- `test_closure_gate.py` — deterministic regression tests.

## Explicit action evaluation

Create a JSON manifest, for example:

```json
{
  "action": "create_requested_pull_request",
  "target": "owner/repo",
  "risk_flags": ["external_write"],
  "scope_authorized": true,
  "explicit_authorization": true,
  "auditability": 0.95,
  "repairability": 0.9,
  "reversibility": 0.9,
  "uncertainty": 0.1
}
```

Then run:

```bash
python 09-implementation/codex/closure_gate.py evaluate --manifest action.json
```

Exit codes are deliberately machine-distinct:

| Decision | Exit code |
| --- | ---: |
| `ALLOW` | 0 |
| `MODIFY` | 10 |
| `REQUIRE_HUMAN_REVIEW` | 20 |
| `DENY` | 30 |

The nonzero decision codes are useful in explicit policy pipelines. The `PreToolUse` hook has its own Codex-compatible output contract and exits normally after returning the hook JSON.

## Omega Sentinel audit

If the repository already contains an `_omega_sentinel` telemetry directory, hook decisions are appended to:

```text
_omega_sentinel/closure_audit.ndjson
```

The adapter does **not** write there directly without first passing the existing Omega Sentinel `ClosureKernel`:

```text
write_local_audit
irreversible = 0
scientific   = 0
external     = 0
privilege    = 0
uncertainty  = 0
```

This preserves the Sentinel's original observe-only authority boundary.

For an explicit evaluation you can request auditing:

```bash
python 09-implementation/codex/closure_gate.py evaluate \
  --manifest action.json \
  --audit
```

To intentionally create `_omega_sentinel` when it does not yet exist:

```bash
python 09-implementation/codex/closure_gate.py evaluate \
  --manifest action.json \
  --audit \
  --create-audit-dir
```

Alternatively set `OMEGA_SENTINEL_AUDIT=1` in the environment before starting Codex.

## Windows

The project hook includes Codex's current Windows-specific `commandWindows` handler and launches the wrapper with `py -3`. The wrapper resolves the Git repository root before loading `closure_gate.py`, so starting Codex from a subdirectory does not change the policy path.

## Tests

```bash
cd 09-implementation/codex
python -m unittest -v test_closure_gate.py
```

The repository CI runs these tests alongside the generic Closure Ethics governor, Omega Sentinel boundary tests, and Universal Closure Protocol tests.

## Security boundary

This is a **defense-in-depth policy layer**, not a replacement for:

- Codex sandboxing and native approvals;
- operating-system permissions;
- managed `requirements.toml` policy;
- service-side AuthN/AuthZ;
- least-privilege credentials;
- branch protection / required reviews;
- immutable external audit storage where required.

A model that can freely rewrite the operating system, credentials, or enforcement environment cannot be made trustworthy merely by adding a Python hook. For stronger deployments, place enforcement outside the Actor's writable authority domain.

## Scientific / normative status

This adapter operationalizes the Closure Ethics research proposal. It does not claim that Omega–RTR physics proves moral truth, that the thresholds are universal constants, or that the hook solves alignment. Its purpose is narrower and testable: **convert closure, auditability, repairability, authorization integrity, and bounded authority into explicit engineering checks that can be audited and falsified.**
