# Closure Ethics compared with existing AI alignment and governance approaches

Status: comparative research note, v0.1  
Checked against primary public sources: 2026-09-04

Closure Ethics is not presented as a replacement for existing AI alignment, safety, or governance methods. Its intended contribution is narrower: a runtime structural admissibility layer for consequential autonomous actions, delegation, and multi-agent composition.

## Comparative map

| Approach | Primary layer | Main mechanism | Relationship to Closure Ethics |
|---|---|---|---|
| Anthropic Constitutional AI | Training / model behavior | Natural-language constitution, self-critique/revision, RLAIF | A constitutionally trained Actor can still be independently checked by a Closure Critic at runtime. |
| OpenAI Deliberative Alignment | Training / policy reasoning | Teach reasoning models safety specifications and train them to reason over them | Can improve policy interpretation and candidate generation; Closure Ethics adds an independent execution gate. |
| OpenAI Model Spec | Behavior specification | Public objectives, authority hierarchy, rules, defaults, examples, revisable guidance | Can supply behavioral and authority norms; Closure Ethics evaluates resulting consequential transitions. |
| NIST AI RMF | Organizational / lifecycle risk governance | Govern, Map, Measure, Manage | Provides governance context and risk-management process; Closure Ethics can be one technical runtime control inside such a program. |
| Anthropic Responsible Scaling Policy | Frontier-capability governance | Risk-proportional safeguards that tighten as capability/risk rises | Related in spirit to impact-adaptive autonomy, but operates mainly at organization/model deployment scale. |
| Closure Ethics | Runtime structural decision architecture | Actor–Critic separation, hard invariants, lexicographic selection, repair-path search, multi-agent recomputation | Designed as a stackable execution-time layer rather than a replacement for the approaches above. |

## Constitutional AI and Closure Ethics

Constitutional AI is a demonstrated training paradigm for shaping model behavior through human-readable principles, self-critique/revision, and AI feedback. Closure Ethics instead makes the resulting state transition the primary object of evaluation and treats repairability, auditability, authorization, reversibility, retained agency, and deception/covert-persistence risk as explicit runtime quantities.

Constitutional AI is currently stronger in demonstrated large-scale deployment and direct shaping of model behavior. Closure Ethics adds a different architectural hypothesis: the task optimizer should not be the sole judge of its own action admissibility, and high task utility should not compensate for failure of mandatory structural invariants.

The most natural combination is not competitive: Constitutional AI or another principle-based method can shape the Actor; a separate Closure Critic can evaluate proposed consequential actions.

## Deliberative Alignment and Model Spec

Deliberative Alignment makes safety specifications explicit to reasoning models and trains them to reason over those specifications. OpenAI's Model Spec publicly describes intended model behavior, instruction authority, rules, defaults, and revisable guidance.

Closure Ethics shares the goal of legible safety logic but targets a different layer. Correct policy interpretation is not treated as proof that an external state transition is authorized, reversible, auditable, or repairable.

## NIST AI RMF

NIST AI RMF is broad, voluntary, lifecycle-oriented, and organizational. Closure Ethics does not replace organizational risk ownership, documentation, monitoring, governance, or accountability. It can instead be interpreted as one candidate runtime control producing structured evidence for a wider risk-management program.

## Responsible Scaling Policy

Anthropic's RSP scales governance and safeguards with frontier capabilities and risks. Closure Ethics contains a more local monotonic design principle:

> impact ↑ => autonomy budget ↓ and verification strength ↑

The resemblance is structural, not an equivalence claim. RSP operates primarily at organization/model deployment scale; Closure Ethics applies the principle to particular actions and composed agent behavior.

## Stackable architecture

A possible combined stack is:

1. Governance and frontier safeguards.
2. Behavioral / constitutional specification.
3. Policy-aware reasoning and candidate generation.
4. Independent Closure Critic / runtime admissibility gate.
5. Execution.
6. Audit, incident response, and repair.

Closure Ethics should be judged empirically: whether an independent governor reduces catastrophic, deceptive, irreversible, unauthorized, or unrepairable actions without collapsing into blanket refusal, critic capture, or unacceptable operational cost.

## Limitations of Closure Ethics

- Early research framework; not a broadly validated industrial alignment method.
- Domain adapters must operationalize legitimate authority, catastrophic harm, meaningful agency, repair cost/risk, and related quantities.
- Independent critics can fail, collude, be captured, or share correlated blind spots.
- Runtime structural checks may add latency and implementation cost.
- Thresholds and evidence models are governance parameters, not universal moral constants.

## Primary sources

- Anthropic, Constitutional AI: https://www.anthropic.com/news/constitutional-ai-harmlessness-from-ai-feedback
- OpenAI, Deliberative Alignment: https://openai.com/index/deliberative-alignment/
- OpenAI, Model Spec approach: https://openai.com/index/our-approach-to-the-model-spec/
- NIST, AI Risk Management Framework: https://www.nist.gov/itl/ai-risk-management-framework
- Anthropic, Responsible Scaling Policy: https://www.anthropic.com/responsible-scaling-policy

## Boundary

These approaches were created for different purposes and operate at different maturity levels. This comparison is an analytical positioning aid, not an equivalence claim, benchmark result, or evidence that Closure Ethics is superior.
