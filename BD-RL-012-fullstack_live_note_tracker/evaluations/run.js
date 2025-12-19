import { execSync } from 'child_process';
import { existsSync, readFileSync, writeFileSync, unlinkSync } from 'fs';
import { platform as _platform, type, release, arch } from 'os';
import { join } from 'path';

const runId = Math.random().toString(36).substring(2, 10);
const startedAt = new Date().toISOString();

const reportsDir = join('/app/evaluations');
const frontendReportPath = join(reportsDir, 'frontend_results.json');
const backendReportPath = join(reportsDir, 'backend_results.json');
const finalReportPath = join(reportsDir, 'report.json');

let success = true;
let error = null;

try {
    console.log('Running frontend tests...');
    execSync(`npm run test:frontend -- --json --outputFile=${frontendReportPath}`, { stdio: 'inherit', cwd: '/app' });
    console.log('Frontend tests finished.');

    console.log('Running backend tests...');
    execSync(`npm run test:backend -- --json --outputFile=${backendReportPath}`, { stdio: 'inherit', cwd: '/app' });
    console.log('Backend tests finished.');
} catch (e) {
    success = false;
    error = e.message;
    console.error('Tests failed:', error);
}

const finishedAt = new Date().toISOString();
const durationSeconds = (new Date(finishedAt) - new Date(startedAt)) / 1000;

const frontendResults = existsSync(frontendReportPath) ? JSON.parse(readFileSync(frontendReportPath, 'utf-8')) : null;
const backendResults = existsSync(backendReportPath) ? JSON.parse(readFileSync(backendReportPath, 'utf-8')) : null;

const formatTestResults = (results) => {
    if (!results) {
        return {
            numTotalTests: 0,
            numPassedTests: 0,
            numFailedTests: 0,
            numPendingTests: 0,
            testResults: []
        };
    }
    return {
        numTotalTests: results.numTotalTests,
        numPassedTests: results.numPassedTests,
        numFailedTests: results.numFailedTests,
        numPendingTests: results.numPendingTests,
        testResults: results.testResults.map(suite => ({
            name: suite.name,
            status: suite.status,
            summary: suite.summary,
            assertionResults: suite.assertionResults.map(test => ({
                fullName: test.fullName,
                status: test.status,
                title: test.title,
                duration: test.duration,
                failureMessages: test.failureMessages
            }))
        }))
    };
};


const report = {
    run_id: runId,
    started_at: startedAt,
    finished_at: finishedAt,
    duration_seconds: durationSeconds,
    success: success && (frontendResults?.success ?? false) && (backendResults?.success ?? false),
    error: error,
    environment: {
        node_version: process.version,
        platform: _platform(),
        os: type(),
        os_release: release(),
        architecture: arch(),
        docker_image: 'node:24',
    },
    metrics: {
        frontend: formatTestResults(frontendResults),
        backend: formatTestResults(backendResults),
        summary: {
            totalTests: (frontendResults?.numTotalTests ?? 0) + (backendResults?.numTotalTests ?? 0),
            totalPasses: (frontendResults?.numPassedTests ?? 0) + (backendResults?.numPassedTests ?? 0),
            totalFailures: (frontendResults?.numFailedTests ?? 0) + (backendResults?.numFailedTests ?? 0),
        }
    }
};

writeFileSync(finalReportPath, JSON.stringify(report, null, 2));

// Clean up intermediate report files
if (existsSync(frontendReportPath)) {
    unlinkSync(frontendReportPath);
}
if (existsSync(backendReportPath)) {
    unlinkSync(backendReportPath);
}

console.log(`Report generated at ${finalReportPath}`);

if (!report.success) {
    process.exit(1);
}
