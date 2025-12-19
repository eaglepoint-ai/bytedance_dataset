#!/usr/bin/env node
const { spawn } = require('child_process');
const fs = require('fs');
const os = require('os');
const path = require('path');
const crypto = require('crypto');

function nowIso() {
  return new Date().toISOString();
}

function genId(len = 8) {
  return crypto.randomBytes(Math.ceil(len / 2)).toString('hex').slice(0, len);
}

function ensureDir(dir) {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

function run(cmd, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { stdio: ['ignore', 'pipe', 'pipe'], ...options });
    let stdout = '';
    let stderr = '';
    child.stdout.on('data', (d) => (stdout += d.toString()));
    child.stderr.on('data', (d) => (stderr += d.toString()));
    child.on('close', (code) => {
      resolve({ code, stdout, stderr });
    });
    child.on('error', reject);
  });
}

async function runBackend(jestJsonPath) {
  const res = await run('npm', ['test', '--', `--json`, `--outputFile=${jestJsonPath}`], {
    cwd: path.join(process.cwd(), 'repository_after', 'backend'),
    env: { ...process.env, NODE_ENV: 'test' }
  });
  return res;
}

async function runFrontend(vitestJsonPath) {
  const res = await run('npx', ['vitest', 'run', '--reporter=json'], {
    cwd: path.join(process.cwd(), 'repository_after', 'frontend'),
    env: { ...process.env, NODE_ENV: 'test' }
  });
  // Vitest prints JSON to stdout; save it
  try {
    fs.writeFileSync(vitestJsonPath, res.stdout || '{}', 'utf-8');
  } catch (e) {
    // ignore
  }
  return res;
}

function safeJsonRead(p) {
  try {
    return JSON.parse(fs.readFileSync(p, 'utf-8'));
  } catch (e) {
    return null;
  }
}

function summarizeVitest(json) {
  if (!json || typeof json !== 'object') {
    return {
      numTotalTests: 0,
      numPassedTests: 0,
      numFailedTests: 0,
      numPendingTests: 0,
      testResults: []
    };
  }
  // Vitest JSON reporter structure may vary; attempt to extract common fields
  const summary = {
    numTotalTests: json?.stats?.tests || json?.numTotalTests || 0,
    numPassedTests: json?.stats?.passed || json?.numPassedTests || 0,
    numFailedTests: json?.stats?.failed || json?.numFailedTests || 0,
    numPendingTests: json?.stats?.skipped || json?.numPendingTests || 0,
    testResults: []
  };

  const files = json?.testResults || json?.results || json?.files || [];
  for (const file of files) {
    const assertions = [];
    const tests = file?.assertionResults || file?.tests || [];
    for (const t of tests) {
      assertions.push({
        fullName: t?.fullname || `${t?.suite || ''} ${t?.name || t?.title || ''}`.trim(),
        status: t?.status || (t?.error ? 'failed' : 'passed'),
        title: t?.name || t?.title || '',
        duration: t?.duration || 0,
        failureMessages: t?.errors ? t.errors.map(e => e.message || String(e)) : []
      });
    }
    summary.testResults.push({
      name: file?.name || file?.file || file?.path || '',
      status: (file?.failed || 0) > 0 ? 'failed' : 'passed',
      summary: '',
      assertionResults: assertions
    });
  }
  return summary;
}

function summarizeJest(json) {
  if (!json || typeof json !== 'object') {
    return {
      numTotalTests: 0,
      numPassedTests: 0,
      numFailedTests: 0,
      numPendingTests: 0,
      testResults: []
    };
  }
  return {
    numTotalTests: json.numTotalTests || 0,
    numPassedTests: json.numPassedTests || 0,
    numFailedTests: json.numFailedTests || 0,
    numPendingTests: json.numPendingTests || 0,
    testResults: json.testResults || []
  };
}

async function main() {
  const started_at = nowIso();
  const run_id = genId(8);
  const tmpDir = path.join(process.cwd(), 'evaluation', 'tmp');
  ensureDir(tmpDir);
  const backendJsonPath = path.join(tmpDir, 'backend_results.json');
  const frontendJsonPath = path.join(tmpDir, 'frontend_results.json');

  const envInfo = {
    node_version: process.version,
    platform: process?.platform || 'linux',
    os: os.type(),
    os_release: os.release(),
    architecture: os.arch(),
    docker_image: process.env.DOCKER_IMAGE || 'node:18-alpine'
  };

  let success = true;
  let error = null;

  // Run tests
  const be = await runBackend(backendJsonPath);
  if (be.code !== 0) {
    success = false;
    error = error || `Backend tests failed: ${be.stderr}`;
  }

  const fe = await runFrontend(frontendJsonPath);
  // Vitest exits non-zero on failures; capture
  if (fe.code !== 0) {
    success = false;
    error = error || `Frontend tests failed: ${fe.stderr}`;
  }

  const backendJson = safeJsonRead(backendJsonPath);
  const frontendJson = safeJsonRead(frontendJsonPath);

  const backendMetrics = summarizeJest(backendJson);
  const frontendMetrics = summarizeVitest(frontendJson);

  const finished_at = nowIso();
  const duration_seconds = (new Date(finished_at).getTime() - new Date(started_at).getTime()) / 1000;

  const summary = {
    totalTests: (backendMetrics.numTotalTests || 0) + (frontendMetrics.numTotalTests || 0),
    totalPasses: (backendMetrics.numPassedTests || 0) + (frontendMetrics.numPassedTests || 0),
    totalFailures: (backendMetrics.numFailedTests || 0) + (frontendMetrics.numFailedTests || 0)
  };

  const report = {
    run_id,
    started_at,
    finished_at,
    duration_seconds,
    success,
    error,
    environment: envInfo,
    metrics: {
      frontend: frontendMetrics,
      backend: backendMetrics,
      summary
    }
  };

  const outPath = path.join(process.cwd(), 'evaluation', 'report.json');
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2), 'utf-8');
  console.log(`Test report written to ${outPath}`);
}

main().catch((e) => {
  const outPath = path.join(process.cwd(), 'evaluation', 'report.json');
  const started_at = nowIso();
  const report = {
    run_id: genId(8),
    started_at,
    finished_at: nowIso(),
    duration_seconds: 0,
    success: false,
    error: e?.message || String(e),
    environment: {
      node_version: process.version,
      platform: process?.platform || 'linux',
      os: os.type(),
      os_release: os.release(),
      architecture: os.arch(),
      docker_image: process.env.DOCKER_IMAGE || 'node:18-alpine'
    },
    metrics: {
      frontend: { numTotalTests: 0, numPassedTests: 0, numFailedTests: 0, numPendingTests: 0, testResults: [] },
      backend: { numTotalTests: 0, numPassedTests: 0, numFailedTests: 0, numPendingTests: 0, testResults: [] },
      summary: { totalTests: 0, totalPasses: 0, totalFailures: 0 }
    }
  };
  try { fs.writeFileSync(outPath, JSON.stringify(report, null, 2), 'utf-8'); } catch {}
  process.exit(1);
});
