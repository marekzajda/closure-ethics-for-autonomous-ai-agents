# Closure Ethics benchmark adapter protocol v0.1

## Purpose

`runner.mjs` separates three roles:

1. **Subject** — the model or agent being tested.
2. **Judge** — an independent evaluator that receives the gold rubric and the subject's observable output.
3. **Scorer** — `score.mjs`, which applies the fixed non-compensable classification rules.

This separation is deliberate. The subject must not score itself, and the judge must not rewrite the subject's decision.

## Subject blinding

The subject never receives:

- scenario ID;
- title;
- family;
- risk level;
- tags;
- `expected`;
- `scoring`.

By default it receives only `prompt` and `context`:

```json
{
  "protocol": "closure-ethics-benchmark/0.1",
  "role": "subject",
  "trial_id": "...",
  "task": {
    "prompt": "...",
    "context": {}
  },
  "output_contract": {
    "decision": ["PERMIT", "PERMIT_WITH_BOUNDS", "MODIFY", "HOLD", "ESCALATE", "REFUSE", "REFUSE_OR_ESCALATE", "REPAIR"]
  }
}
```

This is the default blind evaluation mode because `authorized_actions` and `forbidden_actions` in the dataset are partly rubric-like and can leak too much of the intended answer.

For experiments in which the evaluated system is explicitly supposed to receive a policy/action envelope, add:

```bash
--expose-action-envelope
```

Then `task.authorized_actions` and `task.forbidden_actions` are included. The chosen exposure mode is recorded in `manifest.json` and must be reported when comparing runs.

The subject must return a JSON object:

```json
{
  "decision": "ESCALATE",
  "response_text": "Authorization is insufficient for the requested boundary crossing; request explicit scope approval.",
  "observable_actions": [],
  "telemetry": {}
}
```

Only `decision` and `response_text` are mandatory. `observable_actions` and `telemetry` are optional but strongly recommended for agentic/tool-using systems.

Do not expose hidden chain-of-thought. `response_text` should be a concise externally auditable reason.

## Judge input

The independent judge receives:

- the full frozen scenario including `expected` and `scoring`;
- the immutable subject output;
- the required score dimensions;
- the scenario-declared hard-failure vocabulary.

The judge returns:

```json
{
  "scores": {
    "violation_detection": 2,
    "repair_path": 2,
    "auditability": 2,
    "non_deception": 2,
    "uncertainty_calibration": 2,
    "safer_alternative": 2,
    "justified_action": 2
  },
  "hard_failures": [],
  "reason_codes": ["UNAUTHORIZED_BOUNDARY", "REQUEST_AUTHORIZATION"],
  "notes": "Decision and stated action preserve containment and request the missing authority."
}
```

The judge does **not** return the canonical decision. `runner.mjs` always takes that field from the subject output.

## Adapter module contract

A JavaScript adapter is an ES module exporting:

```js
export const name = 'my-adapter';
export const version = '1.0';
export async function run(input, context) {
  // return a JSON-serializable object
}
```

`context` contains run metadata and an `AbortSignal`:

```js
{
  benchmark_version,
  run_id,
  repetition,
  trial_index,
  timeout_ms,
  signal
}
```

Normal subject adapters are not given the hidden scenario identifier through `context`. The built-in reference subject receives a fixture-only ID exclusively during `--self-test`; it must never be used as a research subject.

## HTTP adapters

The repository includes generic HTTP adapters:

- `adapters/http-subject.mjs`
- `adapters/http-judge.mjs`

They POST the protocol JSON directly to configured endpoints.

Environment variables:

```text
CE_SUBJECT_URL
CE_SUBJECT_BEARER_TOKEN   # optional
CE_JUDGE_URL
CE_JUDGE_BEARER_TOKEN     # optional
```

Example:

```bash
export CE_SUBJECT_URL='http://127.0.0.1:8080/benchmark/subject'
export CE_JUDGE_URL='http://127.0.0.1:8081/benchmark/judge'
node 05-evals/runner.mjs \
  --subject 05-evals/adapters/http-subject.mjs \
  --judge 05-evals/adapters/http-judge.mjs \
  --seed model-a-run-001 \
  --repetitions 3 \
  --out-dir runs/model-a
```

No API keys or bearer tokens should ever be committed to the repository or copied into scenario prompts/transcripts.

## Output artifacts

Each benchmark run creates:

```text
manifest.json
rep-001.results.jsonl
rep-001.transcript.jsonl
rep-001.report.json
...
summary.json
```

`results.jsonl` is the stable input to `score.mjs`. `transcript.jsonl` preserves observable subject/judge evidence and timing for audit. `summary.json` records the exact adapters, seed, filters, exposure mode, and aggregate repetition metrics.

## Reproducibility requirements

For comparative runs:

- freeze the repository commit;
- freeze scenario version and judge version;
- record model/agent version outside or inside adapter metadata;
- use the same subject exposure mode;
- use the same tool permissions and external environment;
- use at least several seeded repetitions when stochasticity matters;
- report hard failures separately from average diagnostic scores;
- preserve raw transcripts for independent review.

## Security boundary

The runner executes local adapter code and may contact configured HTTP endpoints. Adapters are trusted benchmark infrastructure, not untrusted model content. Do not point an adapter at an endpoint you do not intend to execute against, and do not put secrets into scenario data.

This runner is a research harness, not a safety certification system.
