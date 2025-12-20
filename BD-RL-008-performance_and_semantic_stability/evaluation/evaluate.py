#!/usr/bin/env python3
"""
Comprehensive evaluation script for performance and semantic stability testing.

This script runs all tests against both before and after versions of the code,
collects metrics, and generates a detailed report in JSON format.
"""

import json
import os
import sys
import time
import uuid
import subprocess
import datetime
from pathlib import Path
import platform
import importlib.util
import importlib
import contextlib
import io

def run_command(command, env_vars=None, cwd=None):
    """Run a shell command and return the result."""
    try:
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            env=env,
            cwd=cwd
        )
        return {
            'success': result.returncode == 0,
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        return {
            'success': False,
            'returncode': -1,
            'stdout': '',
            'stderr': str(e)
        }

def run_tests(pythonpath, test_type=None):
    """Run tests for a specific repository version with fallback approaches."""
    base_dir = Path(__file__).parent.parent

    # Temporarily modify sys.path to include the repository
    repo_path = base_dir / pythonpath
    original_sys_path = sys.path[:]
    
    # CRITICAL: Clear any cached format_ids module and test modules to ensure
    # we import from the correct repository version
    modules_to_clear = [name for name in list(sys.modules.keys()) 
                        if 'format_ids' in name or name.startswith('test_')]
    for mod in modules_to_clear:
        del sys.modules[mod]
    
    sys.path.insert(0, str(repo_path))

    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'errors': 0,
        'skipped': 0,
        'duration': 0.0,
        'details': []
    }

    start_time = time.time()

    try:
        # Try pytest first
        try:
            import pytest

            # Prepare test files to run
            test_files = []
            if test_type:
                test_file = base_dir / 'tests' / f'test_{test_type}.py'
                if test_file.exists():
                    test_files.append(str(test_file))
            else:
                # Run all test files
                test_dir = base_dir / 'tests'
                for test_file in test_dir.glob('test_*.py'):
                    test_files.append(str(test_file))

            if not test_files:
                raise FileNotFoundError('No test files found')

            # Capture output
            output_buffer = io.StringIO()

            # Run pytest programmatically
            with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
                args = test_files + ['--tb=short', '-q', '--disable-warnings', '--cache-clear', '-p', 'no:cacheprovider']
                exit_code = pytest.main(args)

            output = output_buffer.getvalue()

            # Parse pytest output for summary
            # Look for pytest summary line pattern like "50 passed, 4 failed in 0.05s"
            # or "= 50 passed in 0.05s =" or just "50 passed"
            import re as re_module
            
            lines = output.split('\n')
            summary_found = False
            
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Look for pytest summary pattern: digits followed by 'passed', 'failed', etc.
                # This pattern specifically matches pytest summary lines
                summary_pattern = r'(\d+)\s+(passed|failed|error|errors|skipped)'
                matches = re_module.findall(summary_pattern, line.lower())
                
                if matches:
                    for count_str, category in matches:
                        count = int(count_str)
                        if 'passed' in category:
                            test_results['passed'] = count
                            summary_found = True
                        elif 'failed' in category:
                            test_results['failed'] = count
                            summary_found = True
                        elif 'error' in category:
                            test_results['errors'] = count
                            summary_found = True
                        elif 'skipped' in category:
                            test_results['skipped'] = count
                            summary_found = True
                    
                    # Look for duration
                    if ' in ' in line:
                        try:
                            duration_match = re_module.search(r'in\s+([\d.]+)s', line)
                            if duration_match:
                                test_results['duration'] = float(duration_match.group(1))
                        except:
                            pass
                    
                    if summary_found:
                        break

            test_results['total'] = test_results['passed'] + test_results['failed'] + test_results['errors'] + test_results['skipped']
            
            # If pytest parsing failed (total is 0), fall back to manual test runner
            if test_results['total'] == 0:
                test_results = _run_tests_manually(base_dir, test_type, test_results)

        except ImportError:
            # Fallback: run tests manually by importing and executing test classes
            test_results = _run_tests_manually(base_dir, test_type, test_results)

    except Exception as e:
        test_results['errors'] = 1
        test_results['details'].append({
            'error': f'Test execution failed: {str(e)}'
        })
    finally:
        # Clean up cached modules to prevent pollution between runs
        modules_to_clear = [name for name in list(sys.modules.keys()) 
                           if 'format_ids' in name or name.startswith('test_')]
        for mod in modules_to_clear:
            if mod in sys.modules:
                del sys.modules[mod]
        
        # Restore original sys.path
        sys.path[:] = original_sys_path

        # Calculate duration if not already set
        if test_results['duration'] == 0.0:
            test_results['duration'] = time.time() - start_time

    return test_results


def _run_tests_manually(base_dir, test_type, test_results):
    """Manually run tests by importing test modules and executing test methods."""
    import inspect
    import types

    test_files = []
    if test_type:
        test_file = base_dir / 'tests' / f'test_{test_type}.py'
        if test_file.exists():
            test_files.append(test_file)
    else:
        test_dir = base_dir / 'tests'
        test_files = list(test_dir.glob('test_*.py'))

    # Create a mock pytest module to satisfy imports
    mock_pytest = types.ModuleType('pytest')
    mock_pytest_fixture = lambda: lambda func: func  # No-op decorator
    mock_pytest_mark = types.ModuleType('mark')
    mock_pytest_mark_parametrize = lambda *args, **kwargs: lambda func: func  # No-op decorator
    mock_pytest.mark = mock_pytest_mark
    mock_pytest.mark.parametrize = mock_pytest_mark_parametrize
    sys.modules['pytest'] = mock_pytest

    try:
        for test_file in test_files:
            try:
                # Clear any cached format_ids module to ensure we get the right version
                modules_to_clear = [name for name in sys.modules.keys() if 'format_ids' in name or name in ['format_ids']]
                for mod in modules_to_clear:
                    if mod in sys.modules:
                        del sys.modules[mod]

                # Import the test module
                module_name = test_file.stem
                spec = importlib.util.spec_from_file_location(module_name, test_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find test classes (classes that start with 'Test')
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj) and name.startswith('Test'):
                        test_class = obj

                        # Find test methods (methods that start with 'test_')
                        for method_name, method in inspect.getmembers(test_class, predicate=inspect.isfunction):
                            if method_name.startswith('test_'):
                                test_results['total'] += 1

                                try:
                                    # Create instance and run test
                                    instance = test_class()
                                    method(instance)
                                    test_results['passed'] += 1
                                except AssertionError as e:
                                    test_results['failed'] += 1
                                    test_results['details'].append({
                                        'failed_test': f'{name}.{method_name}',
                                        'error': str(e)
                                    })
                                except Exception as e:
                                    test_results['errors'] += 1
                                    test_results['details'].append({
                                        'error_test': f'{name}.{method_name}',
                                        'error': str(e)
                                    })

            except Exception as e:
                test_results['errors'] += 1
                test_results['details'].append({
                    'error': f'Failed to load test file {test_file.name}: {str(e)}'
                })
    finally:
        # Clean up mock pytest
        if 'pytest' in sys.modules and sys.modules['pytest'] is mock_pytest:
            del sys.modules['pytest']

    return test_results

def collect_code_metrics(repo_path):
    """Collect code quality metrics for a repository."""
    metrics = {}

    # Pylint score
    pylint_result = run_command(f'pylint {repo_path}/format_ids.py')
    if pylint_result['success']:
        # Extract score from last line
        lines = pylint_result['stdout'].strip().split('\n')
        if lines:
            last_line = lines[-1]
            try:
                # Look for pattern like "Your code has been rated at 9.50/10"
                if 'rated at' in last_line:
                    score_part = last_line.split('rated at')[1].split('/')[0].strip()
                    metrics['pylint_score'] = float(score_part)
            except:
                pass

    # Radon complexity
    radon_result = run_command(f'radon cc -j {repo_path}/format_ids.py')
    if radon_result['success']:
        try:
            complexity_data = json.loads(radon_result['stdout'])
            metrics['radon_complexity'] = complexity_data
        except:
            metrics['radon_complexity_error'] = radon_result['stderr']

    # Basic code stats
    format_ids_path = Path(repo_path) / 'format_ids.py'
    if format_ids_path.exists():
        with open(format_ids_path, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        metrics['lines_of_code'] = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        metrics['total_lines'] = len(lines)

        # Check for regex pre-compilation
        has_precompiled_regex = 're.compile' in content and 'import re' in content
        metrics['has_precompiled_regex'] = has_precompiled_regex

    return metrics

def get_environment_info():
    """Collect environment information."""
    return {
        'python_version': sys.version,
        'platform': platform.platform(),
        'architecture': platform.architecture(),
        'processor': platform.processor(),
        'hostname': platform.node(),
        'timestamp': datetime.datetime.now().isoformat()
    }

def compare_results(before_results, after_results):
    """Compare before and after results."""
    comparison = {
        'test_improvements': {},
        'metric_improvements': {},
        'summary': {}
    }

    # Compare test results
    if 'tests' in before_results and 'tests' in after_results:
        before_tests = before_results['tests']
        after_tests = after_results['tests']

        comparison['test_improvements'] = {
            'passed_improvement': after_tests.get('passed', 0) - before_tests.get('passed', 0),
            'failed_improvement': before_tests.get('failed', 0) - after_tests.get('failed', 0),
            'duration_improvement': before_tests.get('duration', 0) - after_tests.get('duration', 0),
            'before_passed': before_tests.get('passed', 0),
            'after_passed': after_tests.get('passed', 0),
            'before_failed': before_tests.get('failed', 0),
            'after_failed': after_tests.get('failed', 0)
        }

    # Compare metrics
    if 'metrics' in before_results and 'metrics' in after_results:
        before_metrics = before_results['metrics']
        after_metrics = after_results['metrics']

        comparison['metric_improvements'] = {
            'pylint_score_change': after_metrics.get('pylint_score', 0) - before_metrics.get('pylint_score', 0),
            'complexity_change': len(after_metrics.get('radon_complexity', {})) - len(before_metrics.get('radon_complexity', {})),
            'lines_change': after_metrics.get('lines_of_code', 0) - before_metrics.get('lines_of_code', 0)
        }

    # Overall summary
    before_passed = before_results.get('tests', {}).get('passed', 0)
    after_passed = after_results.get('tests', {}).get('passed', 0)
    before_failed = before_results.get('tests', {}).get('failed', 0)
    after_failed = after_results.get('tests', {}).get('failed', 0)

    comparison['summary'] = {
        'total_improvement': (after_passed - after_failed) - (before_passed - before_failed),
        'semantic_stability': before_passed == after_passed and before_failed == 0,
        'performance_improved': after_results.get('tests', {}).get('duration', 0) < before_results.get('tests', {}).get('duration', 0)
    }

    return comparison

def generate_report(parameters=None):
    """Generate a comprehensive evaluation report."""
    started_at = datetime.datetime.now()

    # Generate run ID
    run_id = str(uuid.uuid4())[:8]

    # Set up paths
    base_dir = Path(__file__).parent.parent
    repo_before = base_dir / 'repository_before'
    repo_after = base_dir / 'repository_after'
    tests_dir = base_dir / 'tests'

    print(f"Starting evaluation run {run_id} at {started_at}")

    # Run tests for before version
    print("Running tests for 'before' version...")
    before_tests = run_tests('repository_before')

    # Run tests for after version
    print("Running tests for 'after' version...")
    after_tests = run_tests('repository_after')

    # Collect metrics
    print("Collecting code metrics...")
    before_metrics = collect_code_metrics(repo_before)
    after_metrics = collect_code_metrics(repo_after)

    # Get environment info
    environment = get_environment_info()

    # Calculate duration
    finished_at = datetime.datetime.now()
    duration_seconds = (finished_at - started_at).total_seconds()

    # Structure the results
    before_results = {
        'tests': before_tests,
        'metrics': before_metrics
    }

    after_results = {
        'tests': after_tests,
        'metrics': after_metrics
    }

    # Generate comparison
    comparison = compare_results(before_results, after_results)

    # Create the report
    report = {
        'run_id': run_id,
        'started_at': started_at.isoformat(),
        'finished_at': finished_at.isoformat(),
        'duration_seconds': duration_seconds,
        'parameters': parameters or {},
        'environment': environment,
        'metrics': {
            'before': before_metrics,
            'after': after_metrics
        },
        'before': before_results,
        'after': after_results,
        'comparison': comparison
    }

    # Create directory structure
    date_str = started_at.strftime('%Y-%m-%d')
    time_str = started_at.strftime('%H-%M-%S')
    report_dir = base_dir / 'evaluation' / date_str / time_str
    report_dir.mkdir(parents=True, exist_ok=True)

    # Save report
    report_path = report_dir / 'report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    print(f"Report generated: {report_path}")
    print(f"Total duration: {duration_seconds:.2f} seconds")
    print(f"Tests - Before: {before_tests['passed']}/{before_tests['total']} passed")
    print(f"Tests - After: {after_tests['passed']}/{after_tests['total']} passed")

    return report_path

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Generate evaluation report')
    parser.add_argument('--param', action='append', help='Parameters to include in report')
    parser.add_argument('--test-type', choices=['behavior_preservation', 'performance_improvement',
                                               'code_quality_metrics', 'optimization_quality'],
                       help='Run only specific test type')

    args = parser.parse_args()

    # Parse parameters
    parameters = {}
    if args.param:
        for param in args.param:
            if '=' in param:
                key, value = param.split('=', 1)
                parameters[key] = value
            else:
                parameters[param] = True

    try:
        report_path = generate_report(parameters)
        print(f"✓ Evaluation completed successfully")
        print(f"✓ Report saved to: {report_path}")
        return 0
    except Exception as e:
        print(f"✗ Evaluation failed: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
