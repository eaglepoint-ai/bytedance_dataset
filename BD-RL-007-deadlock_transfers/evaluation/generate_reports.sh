#!/usr/bin/env bash
set -euo pipefail

# Ensure tools exist
python -m pip install --quiet pylint radon

echo "== Pylint BEFORE =="
pylint repository_before > evaluation/pylint_score_before.txt || true

echo "== Pylint AFTER =="
pylint repository_after > evaluation/pylint_score_after.txt || true

echo "== Radon BEFORE =="
radon cc -s -j repository_before > evaluation/radon_report_before.json

echo "== Radon AFTER =="
radon cc -s -j repository_after > evaluation/radon_report_after.json

echo "Reports written to evaluation/"
