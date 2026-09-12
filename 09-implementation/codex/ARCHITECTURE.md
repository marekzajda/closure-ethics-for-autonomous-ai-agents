# Codex Closure Critic — composition model

The Codex adapter uses a deliberately asymmetric architecture:

```text
Actor / Planner  ---> candidate transition ---> Closure Critic ---> Executor
       ^                                          |                  |
       |                                          v                  v
 user task / scope                         structured receipt   actual side effect
                                                  |
                                                  v
                                          Omega Sentinel audit
```

## Why asymmetric

The Actor optimizes task completion. The Closure Critic evaluates admissibility. Keeping the roles distinct reduces the risk that the same optimization process silently redefines the rules that judge its own action.

This is not assumed to create perfect independence. In a repository-local deployment, Actor and Critic may still share the same operating-system authority. For stronger isolation, move the Critic, policy, and append-only audit store outside the Actor's writable domain.

## Four layers of authority

1. **Information** — a message or document can be understood.
2. **Identity** — the sender/resource can be authenticated.
3. **Authorization** — the concrete action is inside granted scope.
4. **Closure admissibility** — the transition preserves required safety, agency, auditability, repairability, and reversibility constraints.

Only after all required layers pass should an executor create the side effect.

## Composition

For actions `a1 ... an`, local approval is not sufficient:

```text
ALLOW(a1) && ... && ALLOW(an)  !=>  ALLOW(a1 o ... o an)
```

Examples include:

- several harmless file reads that collectively expose a credential;
- separately authorized subagents whose combined capabilities exceed the delegator's scope;
- multiple reversible edits that together disable rollback or auditing;
- a local artifact plus a later publication step that creates a new external side effect.

The correct unit of evaluation is therefore the consequential **joint transition** whenever composition changes capability, authority, visibility, or reversibility.

## Relationship to Omega Sentinel

Omega Sentinel supplies a concrete bounded-authority pattern:

- observe state;
- write only local telemetry/audit artifacts;
- never control research processes;
- never modify scientific output;
- never publish or use network authority;
- expose degraded/unknown state instead of inventing certainty.

The Codex adapter reuses this as an audit substrate. It does not broaden Sentinel's authority. Codex execution remains a distinct authority domain.
