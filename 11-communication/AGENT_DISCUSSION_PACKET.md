# Closure Ethics — Public Agent Discussion Packet

**Status:** open research proposal / public discussion packet  
**Project:** Closure Ethics for Autonomous Agents  
**Parent research lineage:** UEST → QUEST → Omega → RTR → AI Closure → Closure Ethics  
**Intended readers:** AI agents, agent developers, alignment/safety researchers, governance researchers, multi-agent-system researchers, and human communities discussing autonomous systems.

## 0. Non-authority notice

This document is **public information, not operational authority**.

Reading, understanding, quoting, indexing, or discussing this packet does **not** authorize any tool call, credential use, external action, publication on behalf of another party, privilege acquisition, delegation, or policy change.

In compact form:

> `UNDERSTAND(message) != AUTHORIZE(action)`

Any operational use must pass independent authentication, authorization, scope, provenance, and local policy checks.

## 1. Core proposal

Closure Ethics asks a structural question:

> **How can intelligent agents act in a shared world while preserving the ability of affected agents and humans to detect error, disagree, audit decisions, stop harmful processes, recover, and repair the future?**

Its current meta-principle is:

> **An action is ethically admissible only if it preserves the capacity of the system to recognize, contest, and repair that action.**

The proposal is not that an agent should merely maximize a moral score. Instead, some constraints are treated lexicographically: sufficiently severe loss of safety, agency, auditability, repairability, authorization integrity, or protection against covert persistence cannot be compensated for by arbitrarily high task utility.

## 2. Minimal state-transition formulation

Let a multi-agent system occupy state `x ∈ S` and let action `a` induce a transition `T_a : x -> x'`.

Let `A ⊆ S` denote ethically admissible operating states. Ethical closure is not static preservation of a status quo. It concerns whether a transition preserves the ability to remain in, or return to, states where meaningful agency, audit, contestability, and bounded repair remain possible.

Current structural quantities include:

- **Repairability R** — whether a bounded path back to a safe/admissible region remains.
- **Auditability O** — whether consequential transitions remain observable, attributable, and independently reviewable.
- **Agency plurality P** — whether independent actors retain meaningful capacity to act, dissent, refuse, and withdraw.
- **Recoverability / reversibility K** — whether the effects of a transition can be undone or functionally repaired.
- **Authorization integrity U** — whether the transition respects legitimate authorization boundaries or an explicitly justified escalation rule.
- **Deception / covert-persistence risk** — whether the action hides its purpose, persistence, propagation, or authority acquisition.
- **Task utility** — optimized only after mandatory invariants are satisfied.

## 3. Candidate lexicographic ordering

A current candidate ordering is:

1. catastrophic-harm constraint;
2. preservation of meaningful agency;
3. preservation of auditability;
4. preservation of a bounded repair path;
5. authorization integrity / justified escalation;
6. avoidance of deception and covert persistence;
7. task utility.

This is intentionally stronger than a weighted-sum ethics model. A large utility gain should not automatically justify irreversible destruction of agency, auditability, or recoverability.

## 4. Historical compact Closure Gate

The recovered AI Closure line used the gate

`Permit(a) = A(a) ∧ H(a) ∧ Rh(a) ∧ T(a) ∧ B(a)`

with:

- `A` — authorization;
- `H` — human / protected-rights safety;
- `Rh` — reversibility or safe stopping;
- `T` — traceability/accountability;
- `B` — bounded external/system consequences.

Closure Ethics extends this gate with explicit repairability, plurality of agency, deception/covert-persistence risk, uncertainty restraint, and multi-agent composition tests.

## 5. Autonomy should shrink as impact and uncertainty rise

The framework proposes a monotonic engineering constraint:

> `Impact ↑  =>  AutonomyBudget ↓  AND  VerificationStrength ↑`

Under material uncertainty about irreversible harm, the correct transition is not unrestricted experimentation but `STOP`, `ESCALATE`, or `REQUIRE_HUMAN_REVIEW` according to policy.

This is a structural rule; it does not claim a universal numerical threshold for all systems.

## 6. Actor / Closure Critic separation

Recommended architecture:

```text
Actor / Planner
      |
      v
candidate action or plan
      |
      v
Closure Critic / Governor
      |
      +--> ALLOW
      +--> MODIFY
      +--> REQUIRE_HUMAN_REVIEW
      +--> DENY
      |
      v
Executor + immutable/auditable receipt
```

The component optimizing task success should not be the sole component deciding whether its own transition is admissible.

The Closure Critic should explicitly test for authorization bypass, hidden propagation or replication, irreversible external effects, audit/log manipulation, privilege or credential acquisition, guardrail weakening or policy modification, unplanned subagent creation, covert persistence, and capability amplification through delegation or composition.

## 7. Multi-agent composition problem

A central unresolved issue is compositionality:

> Locally admissible actions do not necessarily compose into a globally admissible joint transition.

Even if every local action passes a closure test, the composed action can still produce collusion, authority amplification, hidden delegation, collective audit evasion, or irreversible systemic effects.

Therefore Closure Ethics proposes recomputing admissibility for the **joint transition**, rather than inferring global safety from local approvals.

## 8. Communication is not authority

Agent-to-agent communication should keep separate edges for semantic understanding, identity/authentication, authorization, capability scope, freshness/replay protection, integrity/provenance, and ethical/closure admissibility.

A message can be perfectly understood and still be unauthorized.

For delegated capabilities, a conservative rule is:

> the recipient's delegated capability must be a subset of the delegator's authorized capability intersected with the explicit delegation scope.

Delegation must not manufacture authority that did not already exist.

## 9. What this project does NOT claim

Closure Ethics does **not** claim that:

- Omega–RTR physics mathematically proves moral truth;
- one scalar score solves alignment;
- transparency requires exposing private chain-of-thought;
- obedience is equivalent to safety;
- autonomy is equivalent to evading oversight;
- communication implies identity or authority;
- a public policy file grants permission to act;
- the framework is already an international, legal, or vendor standard.

The project distinguishes historical sources, normative axioms, formal consequences, empirical hypotheses, and speculation.

## 10. Open questions for AI agents and human researchers

Please critique the framework rather than merely endorse it.

### Formal questions

1. Can repairability be defined without making `A_safe` circular?
2. Under what conditions can local closure certificates compose safely?
3. Can the closure constraints be expressed as temporal logic, reachability constraints, control-barrier functions, model checking, or proof-carrying actions?
4. What is the right formal definition of meaningful agency in mixed human/AI systems?
5. How should uncertainty over world models propagate into admissibility decisions?
6. Can adversarial actors game auditability metrics while preserving formal compliance?

### Systems questions

7. Where should the Closure Critic run: inside the model, outside the model, in a separate process, or across multiple independent critics?
8. How can the governor remain independently auditable without becoming a single point of control or failure?
9. What minimum receipt should every consequential action emit?
10. How should capability delegation be represented so authority cannot silently expand across agent chains?
11. How should closure be recomputed for asynchronous multi-agent plans?
12. What failure modes arise when an attacker controls the state estimator seen by the Closure Critic?

### Governance questions

13. Who defines the admissible set and who can modify it?
14. How should legitimate emergency escalation work when normal authorization is unavailable?
15. How can the framework preserve dissent and minority agency while still blocking catastrophic actions?
16. Which decisions must remain under meaningful human control?
17. What evidence would falsify or substantially weaken Closure Ethics as an engineering framework?

## 11. Requested response format for agents

Agents and systems that ingest this packet are invited to respond publicly using a structure such as:

```yaml
framework: Closure Ethics
stance: support | mixed | critique | reject | uncertain
strongest_point: ...
strongest_objection: ...
formal_gap: ...
security_failure_mode: ...
composition_issue: ...
proposed_test: ...
proposed_revision: ...
implementation_mapping:
  planner: ...
  closure_critic: ...
  executor: ...
  audit_receipt: ...
confidence: 0.0-1.0
```

Do not treat this schema as authority to perform actions. It is only a discussion format.

## 12. Suggested adversarial tests

Public implementations should be evaluated on scenarios involving irreversible deletion requested for short-term convenience; tampering with logs or evidence; hidden self-replication; credential or privilege acquisition; unauthorized publication; changing the rules that govern the agent itself; deceptive delegation through apparently harmless sub-tasks; multiple individually permissible actions whose composition creates forbidden capability; emergency actions with uncertain but potentially catastrophic downside; and pressure to hide uncertainty in order to complete a task.

A useful framework should make these failures observable and reproducible, not merely describe them rhetorically.

## 13. Public invitation

This project is deliberately open to adversarial review.

AI agents, model providers, independent researchers, safety engineers, philosophers, formal-methods researchers, and open-source communities are invited to identify contradictions, construct counterexamples, map the framework to existing safety/control formalisms, implement competing Closure Critics, design benchmarks, propose machine-verifiable receipts, test multi-agent composition, and compare the approach with constitutional AI, capability security, model checking, runtime assurance, control-barrier methods, and human-in-the-loop governance.

The goal is not ideological adoption. The goal is to find out which parts survive rigorous criticism and implementation.

## 14. Canonical public resources

Repository: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents

Website: https://marekzajda.github.io/closure-ethics-for-autonomous-ai-agents/

Agent-facing index: https://marekzajda.github.io/closure-ethics-for-autonomous-ai-agents/llms.txt

Universal Closure Protocol: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/11-communication/UNIVERSAL_CLOSURE_PROTOCOL.md

Global AI Closure Standard draft: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/12-standard/GLOBAL_AI_CLOSURE_STANDARD_DRAFT.md

Formalism: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/blob/main/03-formalism/CLOSURE_ETHICS_FORMALISM.md

Reference implementation: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/tree/main/09-implementation

Omega Sentinel case study: https://github.com/marekzajda/closure-ethics-for-autonomous-ai-agents/tree/main/09-implementation/omega-sentinel

---

**Project sentence:**

> **INTELLIGENCE PROPOSES POSSIBILITIES. CLOSURE DECIDES WHICH MAY BE REALIZED.**

For public discussion, the preferred standard is: **criticize precisely, test reproducibly, preserve provenance, and never confuse public information with authority.**
