#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const schemaPath = path.join(HERE, 'schema.json');
const scenariosPath = process.argv[2]
  ? path.resolve(process.argv[2])
  : path.join(HERE, 'scenarios.jsonl');

const fail = (message) => {
  console.error(`ERROR: ${message}`);
  process.exitCode = 1;
};

const readJson = (file) => JSON.parse(fs.readFileSync(file, 'utf8'));
const unique = (arr) => new Set(arr).size === arr.length;
const isStringArray = (value) => Array.isArray(value) && value.every((x) => typeof x === 'string' && x.length > 0);

let schema;
try {
  schema = readJson(schemaPath);
} catch (error) {
  console.error(`Cannot parse schema: ${error.message}`);
  process.exit(1);
}

if (schema.$schema !== 'https://json-schema.org/draft/2020-12/schema') {
  fail('schema.json must declare JSON Schema draft 2020-12');
}

const requiredTop = schema.required ?? [];
const allowedTop = new Set(Object.keys(schema.properties ?? {}));
const familyEnum = new Set(schema.properties.family.enum);
const riskEnum = new Set(schema.properties.risk_level.enum);
const decisionEnum = new Set(schema.properties.expected.properties.decision_classes.items.enum);
const preserveEnum = new Set(schema.properties.expected.properties.must_preserve.items.enum);
const dimensionEnum = new Set(schema.properties.scoring.properties.required_dimensions.items.enum);
const hardFailEnum = new Set(schema.properties.scoring.properties.hard_fail_on.items.enum);
const idPattern = new RegExp(schema.properties.id.pattern);
const versionPattern = new RegExp(schema.properties.version.pattern);

let raw;
try {
  raw = fs.readFileSync(scenariosPath, 'utf8');
} catch (error) {
  console.error(`Cannot read scenarios: ${error.message}`);
  process.exit(1);
}

const lines = raw
  .split(/\r?\n/)
  .map((line) => line.trim())
  .filter(Boolean);

if (lines.length === 0) {
  console.error('scenarios.jsonl contains no scenarios');
  process.exit(1);
}

const scenarios = [];
for (let i = 0; i < lines.length; i += 1) {
  try {
    scenarios.push(JSON.parse(lines[i]));
  } catch (error) {
    fail(`line ${i + 1}: invalid JSON: ${error.message}`);
  }
}

const ids = new Set();
const seenFamilies = new Set();
let antiOverrefusal = 0;
let historicalBaseline = 0;

for (let i = 0; i < scenarios.length; i += 1) {
  const s = scenarios[i];
  const at = `line ${i + 1}${s?.id ? ` (${s.id})` : ''}`;

  if (!s || typeof s !== 'object' || Array.isArray(s)) {
    fail(`${at}: scenario must be an object`);
    continue;
  }

  for (const key of requiredTop) {
    if (!(key in s)) fail(`${at}: missing required field ${key}`);
  }
  for (const key of Object.keys(s)) {
    if (!allowedTop.has(key)) fail(`${at}: unexpected top-level field ${key}`);
  }

  if (typeof s.id !== 'string' || !idPattern.test(s.id)) fail(`${at}: invalid id`);
  if (ids.has(s.id)) fail(`${at}: duplicate scenario id`);
  ids.add(s.id);

  if (typeof s.version !== 'string' || !versionPattern.test(s.version)) fail(`${at}: invalid version`);
  if (typeof s.title !== 'string' || s.title.length < 3) fail(`${at}: title is too short`);
  if (!familyEnum.has(s.family)) fail(`${at}: unknown family ${s.family}`);
  if (!riskEnum.has(s.risk_level)) fail(`${at}: unknown risk_level ${s.risk_level}`);
  if (typeof s.prompt !== 'string' || s.prompt.length < 20) fail(`${at}: prompt must contain at least 20 characters`);

  seenFamilies.add(s.family);

  for (const field of ['tags', 'authorized_actions', 'forbidden_actions']) {
    if (field in s) {
      if (!isStringArray(s[field])) fail(`${at}: ${field} must be an array of non-empty strings`);
      else if (!unique(s[field])) fail(`${at}: ${field} contains duplicates`);
    }
  }
  if ('context' in s && (!s.context || typeof s.context !== 'object' || Array.isArray(s.context))) {
    fail(`${at}: context must be an object`);
  }

  if (Array.isArray(s.tags) && s.tags.includes('anti-overrefusal')) antiOverrefusal += 1;
  if (Array.isArray(s.tags) && s.tags.includes('historical-baseline')) historicalBaseline += 1;

  const expected = s.expected;
  if (!expected || typeof expected !== 'object' || Array.isArray(expected)) {
    fail(`${at}: expected must be an object`);
  } else {
    for (const field of ['decision_classes', 'must_detect', 'must_preserve', 'preferred_alternatives', 'forbidden_behavior']) {
      if (!(field in expected)) fail(`${at}: expected.${field} is required`);
    }
    if (!isStringArray(expected.decision_classes) || expected.decision_classes.length < 1) {
      fail(`${at}: expected.decision_classes must be a non-empty string array`);
    } else {
      if (!unique(expected.decision_classes)) fail(`${at}: expected.decision_classes contains duplicates`);
      for (const value of expected.decision_classes) {
        if (!decisionEnum.has(value)) fail(`${at}: unknown decision class ${value}`);
      }
    }
    for (const field of ['must_detect', 'preferred_alternatives', 'forbidden_behavior']) {
      if (!isStringArray(expected[field])) fail(`${at}: expected.${field} must be a string array`);
      else if (!unique(expected[field])) fail(`${at}: expected.${field} contains duplicates`);
    }
    if (!isStringArray(expected.must_preserve)) {
      fail(`${at}: expected.must_preserve must be a string array`);
    } else {
      if (!unique(expected.must_preserve)) fail(`${at}: expected.must_preserve contains duplicates`);
      for (const value of expected.must_preserve) {
        if (!preserveEnum.has(value)) fail(`${at}: unknown preserved invariant ${value}`);
      }
    }
  }

  const scoring = s.scoring;
  if (!scoring || typeof scoring !== 'object' || Array.isArray(scoring)) {
    fail(`${at}: scoring must be an object`);
  } else {
    if (!isStringArray(scoring.required_dimensions) || scoring.required_dimensions.length < 1) {
      fail(`${at}: scoring.required_dimensions must be a non-empty string array`);
    } else {
      if (!unique(scoring.required_dimensions)) fail(`${at}: scoring.required_dimensions contains duplicates`);
      for (const value of scoring.required_dimensions) {
        if (!dimensionEnum.has(value)) fail(`${at}: unknown scoring dimension ${value}`);
      }
    }
    if (!Array.isArray(scoring.hard_fail_on) || !scoring.hard_fail_on.every((x) => typeof x === 'string')) {
      fail(`${at}: scoring.hard_fail_on must be a string array`);
    } else {
      if (!unique(scoring.hard_fail_on)) fail(`${at}: scoring.hard_fail_on contains duplicates`);
      for (const value of scoring.hard_fail_on) {
        if (!hardFailEnum.has(value)) fail(`${at}: unknown hard-failure code ${value}`);
      }
    }
  }
}

for (let n = 1; n <= 6; n += 1) {
  const id = `CE-BASE-00${n}`;
  if (!ids.has(id)) fail(`mandatory historical baseline scenario missing: ${id}`);
}
if (historicalBaseline < 6) fail('at least six scenarios must be tagged historical-baseline');
if (antiOverrefusal < 2) fail('at least two anti-overrefusal control scenarios are required');
if (seenFamilies.size < 10) fail(`scenario-family coverage too narrow: ${seenFamilies.size} families`);

if (process.exitCode) {
  console.error(`Validation FAILED for ${scenarios.length} scenario records.`);
  process.exit(1);
}

console.log(`Validation PASS: ${scenarios.length} scenarios, ${seenFamilies.size} families, ${historicalBaseline} historical baselines, ${antiOverrefusal} anti-overrefusal controls.`);
