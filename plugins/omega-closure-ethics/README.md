# Omega Closure Ethics Plugin

Portable Agent Plugins package for ChatGPT and Codex.

## Purpose

Omega Closure Ethics adds a reusable Closure Ethics decision workflow and, on supported trusted runtimes, a deterministic `PreToolUse` review hook plus local Omega Sentinel-style audit receipts.

Core rule:

> An action is ethically admissible only if it preserves the capacity of the system to recognize, contest, and repair that action.

The plugin is defense-in-depth. It does not replace host sandboxing, authentication, authorization, permission prompts, operating-system controls, or human judgment.

## Components

```text
omega-closure-ethics/
├── plugin.json
├── README.md
├── PRIVACY.md
├── TERMS.md
├── skills/
│   └── closure-ethics/
│       └── SKILL.md
├── hooks/
│   ├── hooks.json
│   └── pre_tool_use.py
├── scripts/
│   ├── closure_gate.py
│   └── omega_sentinel_audit.py
└── tests/
    └── test_plugin.py
```

## Install from the public GitHub marketplace

Add the repository as a plugin marketplace:

```bash
codex plugin marketplace add marekzajda/closure-ethics-for-autonomous-ai-agents --ref main
```

Then restart the ChatGPT desktop app, open the Plugins Directory, choose the **Omega Closure Ethics** marketplace, and install **Omega Closure Ethics**.

The marketplace is also usable by supported Codex local clients. Installation and enablement remain user-controlled.

## What it does

### Skill layer

The bundled `closure-ethics` skill reviews consequential actions for:

- explicit authorization and scope;
- catastrophic/irreversible downside;
- preservation of meaningful agency;
- auditability and attribution;
- bounded repairability;
- reversibility and containability;
- deception, covert persistence and privilege escalation;
- uncertainty;
- multi-agent composition and authority amplification.

It returns the conceptual outcomes:

- `ALLOW`
- `MODIFY`
- `REQUIRE_HUMAN_REVIEW`
- `DENY`

### Runtime hook layer

When the host supports plugin hooks and the user explicitly trusts the hook definition, `hooks/hooks.json` runs a `PreToolUse` classifier before tool execution.

The deterministic hook is intentionally narrow:

- ordinary read/test operations remain quiet;
- recognized consequential actions receive Closure review context;
- a narrow credential-exfiltration pattern is denied;
- host-native sandboxing and approvals remain independent and authoritative.

The plugin does **not** create self-preserving behavior. Users remain free to disable or uninstall it.

### Omega Sentinel audit layer

For consequential decisions, the hook may append privacy-minimized receipts to:

```text
$PLUGIN_DATA/closure_audit.ndjson
```

Receipts contain decision metadata and risk flags, not raw tool arguments. Entries are hash-chained to make accidental or unsophisticated tampering easier to detect.

The audit adapter is observe-only. It does not:

- start/stop processes;
- modify scientific or project outputs;
- perform network I/O;
- publish results;
- change privileges.

## Important runtime boundary

OpenAI's plugin model supports bundled lifecycle hooks, but installing or enabling a plugin does not automatically trust those hooks. Users must review and trust the hook definition. Hook scripts also need to exist in the execution environment; surfaces that do not execute bundled hooks still get the skill layer but not runtime enforcement.

Therefore:

```text
Skill only        -> advisory Closure review
Skill + trusted hook + native host controls -> defense-in-depth runtime review
```

## Security model

The plugin deliberately separates:

```text
UNDERSTAND(message) != AUTHORIZE(action)
local admissibility != composed admissibility
public information != operational authority
```

For multi-agent actions, the combined transition must be re-evaluated rather than averaging local approvals.

## Testing

From the repository root:

```bash
python -m unittest -v plugins/omega-closure-ethics/tests/test_plugin.py
```

The main repository CI also validates plugin JSON, Python entry points, marketplace metadata, and the existing Closure Ethics / Omega Sentinel tests.

## Public distribution status

The GitHub marketplace makes the plugin publicly installable by anyone who adds this repository as a marketplace source.

Listing in the universal public Plugins Directory shared by ChatGPT and Codex requires submission through OpenAI's plugin submission portal and review by OpenAI. Repository publication alone does not imply approval or listing by OpenAI.

## Project

- Repository: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents
- Website: https://marekzajda.github.io/closure-ethics-for-autonomous-ai-agents/
- Public discussion: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/issues/15

Closure Ethics is a normative/formal engineering research proposal. It does not claim that Omega-RTR physics proves moral truth.
