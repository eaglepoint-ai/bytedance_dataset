#!/bin/bash
set -e

case "$1" in
    test-before)
        export PYTHONPATH=/app/repository_before
        pytest -q tests/test_before.py
        ;;
    test-after)
        export PYTHONPATH=/app/repository_after
        pytest -q tests/test_after.py
        ;;
    test-equivalence)
        pytest -q tests/test_calc_score_equivalence.py
        ;;
    test-structure)
        pytest -q tests/test_structure.py
        ;;
    test-all)
        pytest -q tests/test_structure.py tests/test_calc_score_equivalence.py tests/test_before.py tests/test_after.py
        ;;
    evaluate)
        python evaluation/evaluation.py
        ;;
    test-score)
        pytest -q tests/test_score.py
        ;;
    *)
        # If no recognized command, execute whatever was passed
        exec "$@"
        ;;
esac

