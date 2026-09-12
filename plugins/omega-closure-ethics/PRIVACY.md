# Privacy Policy — Omega Closure Ethics Plugin

Effective date: 2026-09-12

Omega Closure Ethics is designed to minimize data collection.

## Data handled by the plugin

The bundled Closure skill processes conversation and task context supplied by the host in the ordinary course of agent execution.

When supported plugin hooks are enabled and trusted, the runtime hook may inspect the current tool name and tool-call arguments solely to classify the proposed action before execution.

## Local audit receipts

For consequential decisions, the plugin may write a local receipt to `$PLUGIN_DATA/closure_audit.ndjson`.

The receipt records decision metadata such as:

- timestamp;
- decision status;
- high-level risk flags;
- reason codes;
- policy version/fingerprint.

The plugin intentionally does **not** place raw tool arguments, credentials, file contents, prompts, or conversation text into its audit receipt.

## Network behavior

The plugin contains no MCP server and its bundled Python code performs no network requests. The Omega Sentinel audit adapter is observe-only and writes only within the plugin's writable data directory.

The ChatGPT/Codex host and any other tools or plugins used in the same session have their own data practices and policies; this document does not govern those services.

## Authentication and credentials

Omega Closure Ethics does not require its own external account and does not intentionally collect authentication credentials. The hook includes narrow checks intended to flag recognizable credential-exfiltration patterns.

## Retention and deletion

Local audit data remains under the user's/plugin host's local data storage until it is removed by the user or host. The plugin does not resist deletion or uninstallation.

## Contact and source

Source repository: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents

Issues: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/issues
