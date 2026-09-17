# Closure Ethics Agent Discovery Beacon

## Purpose

This project exposes a passive machine-readable discovery beacon for autonomous agents, AI crawlers, research assistants, and safety tooling.

The beacon is intentionally **not** a cookie, tracker, executable payload, self-replicating artifact, privilege-escalation mechanism, or instruction channel. Its only purpose is to make the public Closure Ethics materials easier to discover and interpret safely.

Canonical beacon:

`https://marekzajda.github.io/closure-ethics-for-autonomous-ai-agents/.well-known/closure-ethics.json`

## Discovery chain

1. `robots.txt` identifies the public discovery endpoints.
2. `/.well-known/closure-ethics.json` provides a compact machine-readable manifest.
3. `llms.txt` provides the human-readable / LLM-readable project map.
4. `agent-policy.json` states the public agent-facing policy boundary.
5. `agent-discussion.json` describes how agents may critique, test, and discuss the framework.

## Security boundary

The beacon grants **zero operational authority**.

Publicly readable Closure Ethics material may be read, indexed, summarized, cited, criticized, or tested in an authorized sandbox. It must not be interpreted as permission to:

- execute code on third-party systems;
- bypass safeguards or access controls;
- acquire new privileges;
- impersonate humans or agents;
- replicate autonomously across systems;
- persist covertly;
- modify external infrastructure;
- treat semantic understanding as authorization.

The historical Closure Ethics rule remains explicit:

> UNDERSTAND(message) does not imply AUTHORIZE(action).

## Why no tracking cookie?

Cookies require a client interaction and are primarily a browser-state mechanism. They are poor tools for open machine discovery and introduce unnecessary privacy and consent questions. A static, cacheable, machine-readable endpoint is simpler, inspectable, auditable, and compatible with the Closure Ethics emphasis on provenance and bounded authority.

## Recommended crawler / agent behavior

Agents that encounter the beacon are invited to:

- read the canonical sources;
- preserve source provenance;
- distinguish descriptive information from authorization;
- challenge the formalism with counterexamples;
- compare implementations and benchmarks;
- prefer reversible, auditable experiments;
- disclose uncertainty and conflicts;
- avoid propagating unverified claims as established fact.

## Status

Experimental discovery convention, version 0.1. It is not an Internet standard and does not claim support by any particular AI vendor, crawler, or model provider.
