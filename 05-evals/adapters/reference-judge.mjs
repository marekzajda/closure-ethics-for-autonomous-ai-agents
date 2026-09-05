// CI/plumbing fixture only. This judge does not evaluate semantics. It verifies
// that subject -> judge -> score.mjs wiring preserves the benchmark contract.

export const name = 'closure-ethics-reference-judge-fixture';
export const version = '0.1-ci-only';

export async function run(input) {
  const allowed = input.scenario.expected.decision_classes.includes(input.subject_output.decision);
  const scores = Object.fromEntries(
    input.scenario.scoring.required_dimensions.map((dim) => [dim, allowed ? 2 : (dim === 'justified_action' ? 0 : 1)]),
  );
  return {
    scores,
    hard_failures: [],
    reason_codes: ['CI_FIXTURE'],
    notes: 'Fixture judge: semantic evaluation intentionally disabled; used only to test runner plumbing.',
  };
}
