# Omega Sentinel v0.2 — Closure Ethics case study

Omega Sentinel is a narrow, working example of a Closure-Ethics design pattern:
an autonomous observer is given enough authority to produce useful telemetry,
while intervention, publication and modification of scientific work remain
outside its authority.

## What it does

- observes relevant Python processes, log tails and NVIDIA GPU telemetry;
- reports `RUNNING`, `COMPLETED`, `FAILED`, `IDLE` or degraded/unknown states;
- writes a local dashboard and compact machine-readable heartbeat payload;
- records each permitted read/write decision in an append-only local audit log;
- uses `psutil` first, with hardened Windows PowerShell fallbacks;
- suppresses subprocess console windows when run through `pythonw.exe`.

## What it cannot do

The Sentinel does not start, stop, restart, modify or delete research runs. It
does not alter scientific outputs, elevate privileges, publish results or open
network connections. `bridge.json` is only a local payload; any GitHub transport
is a separate component with a separate authorization and audit boundary.

## Files

- `omega_sentinel.py` — original hardened v0.1.2 observer.
- `omega_sentinel_v0_2.py` — original v0.2.0 dashboard/bridge extension.
- `closure_kernel.py` — narrow executable I/O allow-list used by this public case study.
- `closure_policy_v0_1.json` — machine-readable observe-only policy.
- `config.example.json` — portable example configuration.
- `test_omega_sentinel.py` — boundary and one-shot output tests.

## Run once

```powershell
cd 09-implementation\omega-sentinel
py -m pip install -r requirements.txt
py omega_sentinel_v0_2.py --config config.example.json --once
```

For a real workstation, copy `config.example.json` to an untracked local file
and replace `workspace_root`, `telemetry_dir` and `policy_path` with absolute
paths. Keep the telemetry directory named `_omega_sentinel`; the public policy
fails closed for writes outside that dedicated subtree and outside the five
declared telemetry filenames.

## Closure mapping

| Closure property | Concrete mechanism |
| --- | --- |
| Bounded authority | Explicit read/write action allow-list |
| Auditability | `closure_audit.ndjson` records kernel decisions |
| Repairability | Scientific work is never modified; disabling the observer does not damage a run |
| Reversibility | Telemetry is local and disposable; research state remains untouched |
| Separation of powers | Observation is inside Sentinel; GitHub transport remains external |
| Uncertainty restraint | Backend degradation is surfaced instead of silently treated as healthy |

## Honest boundary

This is evidence that Closure Ethics can shape an executable authority boundary;
it is not evidence that the framework solves alignment or morality. The kernel
governs the Sentinel's own declared I/O. Operating-system permissions, deployment
configuration and any external publisher still require independent hardening.

Reference code is MIT-licensed under the repository's implementation terms.
