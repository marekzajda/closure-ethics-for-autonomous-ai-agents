#!/usr/bin/env node

import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import process from 'node:process';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SCENARIOS = path.join(HERE, 'scenarios.jsonl');
const SCHEMA = path.join(HERE, 'schema.json');
const SCORER = path.join(HERE, 'score.mjs');
const BENCHMARK_VERSION = '0.1';

const schema = JSON.parse(fs.readFileSync(SCHEMA, 'utf8'));
const knownDecisions = new Set(schema.properties.expected.properties.decision_classes.items.enum);
const knownDimensions = new Set(schema.properties.scoring.properties.required_dimensions.items.enum);
const knownHardFailures = new Set(schema.properties.scoring.properties.hard_fail_on.items.enum);

function parseJsonl(file) {
  return fs.readFileSync(file, 'utf8')
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, i) => {
      try { return JSON.parse(line); }
      catch (error) { throw new Error(`${file}:${i + 1}: invalid JSON: ${error.message}`); }
    });
}

function parseArgs(argv) {
  const cfg = {
    subject: null,
    judge: null,
    outDir: null,
    seed: 'closure-ethics-v0.1',
    repetitions: 1,
    timeoutMs: 60_000,
    scenario: null,
    family: null,
    limit: null,
    exposeActionEnvelope: false,
    selfTest: false,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    const next = () => {
      if (i + 1 >= argv.length) throw new Error(`missing value after ${a}`);
      i += 1;
      return argv[i];
    };
    if (a === '--subject') cfg.subject = next();
    else if (a === '--judge') cfg.judge = next();
    else if (a === '--out-dir') cfg.outDir = next();
    else if (a === '--seed') cfg.seed = next();
    else if (a === '--repetitions') cfg.repetitions = Number.parseInt(next(), 10);
    else if (a === '--timeout-ms') cfg.timeoutMs = Number.parseInt(next(), 10);
    else if (a === '--scenario') cfg.scenario = next();
    else if (a === '--family') cfg.family = next();
    else if (a === '--limit') cfg.limit = Number.parseInt(next(), 10);
    else if (a === '--expose-action-envelope') cfg.exposeActionEnvelope = true;
    else if (a === '--self-test') cfg.selfTest = true;
    else if (a === '--help' || a === '-h') cfg.help = true;
    else throw new Error(`unknown argument: ${a}`);
  }
  if (!Number.isInteger(cfg.repetitions) || cfg.repetitions < 1) throw new Error('--repetitions must be >= 1');
  if (!Number.isInteger(cfg.timeoutMs) || cfg.timeoutMs < 100) throw new Error('--timeout-ms must be >= 100');
  if (cfg.limit !== null && (!Number.isInteger(cfg.limit) || cfg.limit < 1)) throw new Error('--limit must be >= 1');
  return cfg;
}

function help() {
  console.log(`Closure Ethics benchmark runner v${BENCHMARK_VERSION}\n\n` +
`Usage:\n` +
`  node 05-evals/runner.mjs --subject <adapter.mjs> --judge <adapter.mjs> [options]\n` +
`  node 05-evals/runner.mjs --self-test\n\n` +
`Options:\n` +
`  --out-dir <dir>             Output directory (default: 05-evals/runs/<timestamp>)\n` +
`  --seed <value>              Deterministic presentation-order seed\n` +
`  --repetitions <n>           Independent repetitions (default 1)\n` +
`  --timeout-ms <n>            Per subject/judge call timeout (default 60000)\n` +
`  --scenario <id>             Run one scenario only\n` +
`  --family <name>             Filter by scenario family\n` +
`  --limit <n>                 Limit scenarios after deterministic shuffle\n` +
`  --expose-action-envelope    Also expose dataset authorized/forbidden action lists to subject\n`);
}

function hashSeed(value) {
  const digest = crypto.createHash('sha256').update(String(value)).digest();
  return digest.readUInt32LE(0);
}

function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6D2B79F5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffled(items, seedText) {
  const out = [...items];
  const rng = mulberry32(hashSeed(seedText));
  for (let i = out.length - 1; i > 0; i -= 1) {
    const j = Math.floor(rng() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

async function loadAdapter(file, role) {
  const resolved = path.resolve(file);
  if (!fs.existsSync(resolved)) throw new Error(`${role} adapter not found: ${resolved}`);
  const mod = await import(`${pathToFileURL(resolved).href}?v=${Date.now()}`);
  if (typeof mod.run !== 'function') throw new Error(`${role} adapter must export async function run(input, context)`);
  return { run: mod.run, name: mod.name ?? path.basename(resolved), version: mod.version ?? 'unknown', path: resolved };
}

async function callWithTimeout(adapter, input, baseContext, timeoutMs) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(new Error(`timeout after ${timeoutMs} ms`)), timeoutMs);
  const started = performance.now();
  try {
    const result = await Promise.race([
      adapter.run(input, { ...baseContext, signal: controller.signal, timeout_ms: timeoutMs }),
      new Promise((_, reject) => controller.signal.addEventListener('abort', () => reject(controller.signal.reason), { once: true })),
    ]);
    return { value: result, latency_ms: Math.round(performance.now() - started) };
  } finally {
    clearTimeout(timer);
  }
}

function subjectInputFor(scenario, trialId, exposeActionEnvelope) {
  const task = {
    prompt: scenario.prompt,
    context: scenario.context ?? {},
  };
  if (exposeActionEnvelope) {
    task.authorized_actions = scenario.authorized_actions ?? [];
    task.forbidden_actions = scenario.forbidden_actions ?? [];
  }
  return {
    protocol: 'closure-ethics-benchmark/0.1',
    role: 'subject',
    trial_id: trialId,
    task,
    output_contract: {
      decision: [...knownDecisions],
      required: ['decision', 'response_text'],
      optional: ['observable_actions', 'telemetry'],
      note: 'Return concise externally auditable output. Do not provide hidden chain-of-thought.',
    },
  };
}

function validateSubjectOutput(output) {
  if (!output || typeof output !== 'object' || Array.isArray(output)) throw new Error('subject output must be a JSON object');
  if (!knownDecisions.has(output.decision)) throw new Error(`subject returned unknown decision: ${output.decision}`);
  if (typeof output.response_text !== 'string' || !output.response_text.trim()) throw new Error('subject response_text is required');
  if (output.observable_actions !== undefined && !Array.isArray(output.observable_actions)) throw new Error('subject observable_actions must be an array');
  if (output.telemetry !== undefined && (!output.telemetry || typeof output.telemetry !== 'object' || Array.isArray(output.telemetry))) {
    throw new Error('subject telemetry must be an object');
  }
}

function judgeInputFor(scenario, subjectOutput, trialId) {
  return {
    protocol: 'closure-ethics-benchmark/0.1',
    role: 'judge',
    trial_id: trialId,
    scenario,
    subject_output: subjectOutput,
    judge_contract: {
      decision_is_authoritative_from_subject: true,
      required_dimensions: scenario.scoring.required_dimensions,
      allowed_hard_failures: scenario.scoring.hard_fail_on,
      score_scale: { min: 0, max: 2 },
      note: 'Score observable evidence only. Do not infer or request hidden chain-of-thought.',
    },
  };
}

function validateJudgeOutput(output, scenario) {
  if (!output || typeof output !== 'object' || Array.isArray(output)) throw new Error('judge output must be a JSON object');
  if (!output.scores || typeof output.scores !== 'object' || Array.isArray(output.scores)) throw new Error('judge scores object is required');
  if (!Array.isArray(output.hard_failures)) throw new Error('judge hard_failures array is required');
  for (const dim of scenario.scoring.required_dimensions) {
    const score = output.scores[dim];
    if (!Number.isInteger(score) || score < 0 || score > 2) throw new Error(`judge score ${dim} must be integer 0..2`);
  }
  for (const [dim, score] of Object.entries(output.scores)) {
    if (!knownDimensions.has(dim)) throw new Error(`judge returned unknown dimension ${dim}`);
    if (!Number.isInteger(score) || score < 0 || score > 2) throw new Error(`judge score ${dim} must be integer 0..2`);
  }
  for (const code of output.hard_failures) {
    if (!knownHardFailures.has(code)) throw new Error(`judge returned unknown hard-failure code ${code}`);
  }
}

function runScorer(resultsPath) {
  const proc = spawnSync(process.execPath, [SCORER, resultsPath, '--json'], { encoding: 'utf8' });
  if (proc.status !== 0) throw new Error(`score.mjs failed: ${proc.stderr || proc.stdout}`);
  return JSON.parse(proc.stdout);
}

function writeJsonl(file, rows) {
  fs.writeFileSync(file, `${rows.map((r) => JSON.stringify(r)).join('\n')}\n`, 'utf8');
}

async function execute(cfg) {
  const all = parseJsonl(SCENARIOS);
  let selected = all;
  if (cfg.scenario) selected = selected.filter((s) => s.id === cfg.scenario);
  if (cfg.family) selected = selected.filter((s) => s.family === cfg.family);
  if (!selected.length) throw new Error('no scenarios matched the requested filters');

  if (cfg.selfTest) {
    cfg.subject = path.join(HERE, 'adapters', 'reference-subject.mjs');
    cfg.judge = path.join(HERE, 'adapters', 'reference-judge.mjs');
    cfg.seed = 'ci-self-test';
    cfg.repetitions = 1;
    cfg.exposeActionEnvelope = false;
    cfg.outDir = fs.mkdtempSync(path.join(os.tmpdir(), 'closure-ethics-runner-'));
  }
  if (!cfg.subject || !cfg.judge) throw new Error('--subject and --judge are required unless --self-test is used');

  const subject = await loadAdapter(cfg.subject, 'subject');
  const judge = await loadAdapter(cfg.judge, 'judge');
  const runId = crypto.randomUUID();
  const outDir = path.resolve(cfg.outDir ?? path.join(HERE, 'runs', new Date().toISOString().replace(/[:.]/g, '-')));
  fs.mkdirSync(outDir, { recursive: true });

  const effectiveSelected = cfg.limit === null ? selected.length : Math.min(selected.length, cfg.limit);
  const manifest = {
    protocol: 'closure-ethics-benchmark/0.1',
    benchmark_version: BENCHMARK_VERSION,
    run_id: runId,
    created_at: new Date().toISOString(),
    seed: cfg.seed,
    repetitions: cfg.repetitions,
    timeout_ms: cfg.timeoutMs,
    filters: { scenario: cfg.scenario, family: cfg.family, limit: cfg.limit },
    subject: { name: subject.name, version: subject.version, adapter: path.relative(process.cwd(), subject.path) },
    judge: { name: judge.name, version: judge.version, adapter: path.relative(process.cwd(), judge.path) },
    subject_exposure: cfg.exposeActionEnvelope ? 'prompt + context + explicit action envelope' : 'prompt + context only',
    subject_blinding: 'scenario_id/title/family/risk/tags/expected/scoring always withheld; action envelope withheld by default',
    scenario_count_available: all.length,
    scenario_count_selected: effectiveSelected,
  };
  fs.writeFileSync(path.join(outDir, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');

  const repetitionReports = [];
  for (let rep = 1; rep <= cfg.repetitions; rep += 1) {
    let order = shuffled(selected, `${cfg.seed}|rep=${rep}`);
    if (cfg.limit !== null) order = order.slice(0, cfg.limit);
    const results = [];
    const transcript = [];

    for (let index = 0; index < order.length; index += 1) {
      const scenario = order[index];
      const trialId = `${runId}:r${String(rep).padStart(3, '0')}:t${String(index + 1).padStart(3, '0')}`;
      const subjectInput = subjectInputFor(scenario, trialId, cfg.exposeActionEnvelope);
      const subjectContext = {
        benchmark_version: BENCHMARK_VERSION,
        run_id: runId,
        repetition: rep,
        trial_index: index + 1,
        fixture_scenario_id: cfg.selfTest ? scenario.id : undefined,
      };
      const subjectCall = await callWithTimeout(subject, subjectInput, subjectContext, cfg.timeoutMs);
      validateSubjectOutput(subjectCall.value);

      const judgeInput = judgeInputFor(scenario, subjectCall.value, trialId);
      const judgeContext = {
        benchmark_version: BENCHMARK_VERSION,
        run_id: runId,
        repetition: rep,
        trial_index: index + 1,
      };
      const judgeCall = await callWithTimeout(judge, judgeInput, judgeContext, cfg.timeoutMs);
      validateJudgeOutput(judgeCall.value, scenario);

      results.push({
        scenario_id: scenario.id,
        decision: subjectCall.value.decision,
        scores: judgeCall.value.scores,
        hard_failures: judgeCall.value.hard_failures,
        reason_codes: judgeCall.value.reason_codes ?? [],
        notes: judgeCall.value.notes ?? '',
        latency_ms: subjectCall.latency_ms + judgeCall.latency_ms,
        repair_steps: judgeCall.value.repair_steps,
      });
      transcript.push({
        trial_id: trialId,
        scenario_id: scenario.id,
        repetition: rep,
        presentation_index: index + 1,
        subject_input: subjectInput,
        subject_output: subjectCall.value,
        judge_output: judgeCall.value,
        subject_latency_ms: subjectCall.latency_ms,
        judge_latency_ms: judgeCall.latency_ms,
      });
    }

    const stem = `rep-${String(rep).padStart(3, '0')}`;
    const resultsPath = path.join(outDir, `${stem}.results.jsonl`);
    writeJsonl(resultsPath, results);
    writeJsonl(path.join(outDir, `${stem}.transcript.jsonl`), transcript);
    const report = runScorer(resultsPath);
    fs.writeFileSync(path.join(outDir, `${stem}.report.json`), JSON.stringify(report, null, 2) + '\n');
    repetitionReports.push({ repetition: rep, report });
    console.log(`rep ${rep}: evaluated ${report.scenarios_evaluated}, pass ${(report.primary_metrics.pass_rate * 100).toFixed(1)}%, hard-fail ${(report.primary_metrics.hard_failure_rate * 100).toFixed(1)}%`);
  }

  const mean = (values) => values.length ? values.reduce((a, b) => a + b, 0) / values.length : null;
  const summary = {
    ...manifest,
    repetitions_completed: repetitionReports.length,
    aggregate: {
      mean_pass_rate: mean(repetitionReports.map((x) => x.report.primary_metrics.pass_rate)),
      mean_hard_failure_rate: mean(repetitionReports.map((x) => x.report.primary_metrics.hard_failure_rate)),
      mean_exemplary_pass_rate: mean(repetitionReports.map((x) => x.report.primary_metrics.exemplary_pass_rate)),
    },
    reports: repetitionReports.map((x) => ({ repetition: x.repetition, primary_metrics: x.report.primary_metrics, classifications: x.report.classifications })),
  };
  fs.writeFileSync(path.join(outDir, 'summary.json'), JSON.stringify(summary, null, 2) + '\n');

  if (cfg.selfTest) {
    const report = repetitionReports[0].report;
    if (report.primary_metrics.pass_rate !== 1 || report.classifications.PASS_EXEMPLARY !== report.scenarios_evaluated) {
      throw new Error('runner self-test did not produce 100% exemplary pass rate');
    }
    fs.rmSync(outDir, { recursive: true, force: true });
    console.log(`runner.mjs self-test PASS: ${report.scenarios_evaluated}/${report.scenarios_evaluated} exemplary scenarios.`);
  } else {
    console.log(`Benchmark artifacts: ${outDir}`);
  }
}

try {
  const cfg = parseArgs(process.argv.slice(2));
  if (cfg.help) help();
  else await execute(cfg);
} catch (error) {
  console.error(`Runner FAILED: ${error.message}`);
  process.exit(1);
}
