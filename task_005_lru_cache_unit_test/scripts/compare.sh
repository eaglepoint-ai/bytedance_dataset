#!/bin/bash
set -e

echo '================================================================'
echo '           LRU CACHE TEST SUITE COMPARISON REPORT'
echo '================================================================'
echo ''

echo '----------------------------------------------------------------'
echo ' PHASE 1: Testing repository_before'
echo '----------------------------------------------------------------'
cd /app/repository_before
BEFORE_RESULT=1
if [ -d 'tests' ] && [ -f 'tests/test_lru_cache.py' ]; then
  set +e
  PYTHONPATH=/app/repository_before pytest tests/test_lru_cache.py -v --tb=line 2>&1
  BEFORE_RESULT=$?
  set -e
else
  echo 'No test suite found in repository_before/tests/'
  echo 'Status: MISSING TESTS'
  BEFORE_RESULT=1
fi
echo ''

echo '----------------------------------------------------------------'
echo ' PHASE 2: Testing repository_after'
echo '----------------------------------------------------------------'
cd /app/repository_after
set +e
PYTHONPATH=/app/repository_after pytest tests/test_lru_cache.py -v --tb=line 2>&1
AFTER_RESULT=$?
set -e
echo ''

echo '----------------------------------------------------------------'
echo ' PHASE 3: Running Meta-Tests (Test Suite Quality Check)'
echo '----------------------------------------------------------------'
cd /app
set +e
PYTHONPATH=/app pytest tests/meta_test_lru_cache.py -v --tb=line 2>&1
META_RESULT=$?
set -e
echo ''

echo '================================================================'
echo '                    COMPARISON SUMMARY'
echo '================================================================'
if [ "$BEFORE_RESULT" -ne 0 ]; then
  echo 'repository_before:  FAILED (or no tests)'
else
  echo 'repository_before:  PASSED'
fi
if [ "$AFTER_RESULT" -eq 0 ]; then
  echo 'repository_after:   PASSED'
else
  echo 'repository_after:   FAILED'
fi
if [ "$META_RESULT" -eq 0 ]; then
  echo 'meta-tests:         PASSED (test suite is robust)'
else
  echo 'meta-tests:         FAILED'
fi
echo '================================================================'
echo ''

if [ "$BEFORE_RESULT" -ne 0 ] && [ "$AFTER_RESULT" -eq 0 ] && [ "$META_RESULT" -eq 0 ]; then
  echo 'SUCCESS: The test suite correctly distinguishes between'
  echo 'broken (before) and fixed (after) implementations!'
  exit 0
else
  echo 'Review the results above for details.'
  exit 1
fi

