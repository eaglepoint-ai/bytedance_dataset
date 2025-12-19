#!/usr/bin/env python3
"""
Evaluation runner for Mechanical Refactor (calc_score).

This evaluation script:
- Tests both before and after implementations
- Compares code quality metrics (pylint scores)
- Verifies structural improvements
- Generates structured reports

Run with:
    docker compose run --rm app python evaluation/evaluation.py [options]
"""
import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "repository_before"))
sys.path.insert(0, str(Path(__file__).parent.parent / "repository_after"))


def run_pylint(file_path):
    """Run pylint on a file and extract the score."""
    try:
        result = subprocess.run(
            ["pylint", file_path, "--score=y", "--output-format=json"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                # Find the score in the output
                for item in data:
                    if "score" in item:
                        return {
                            "score": item["score"],
                            "max_score": 10.0,
                        }
            except json.JSONDecodeError:
                pass
        
        # Fallback: parse text output
        output = result.stdout + result.stderr
        for line in output.split("\n"):
            if "rated at" in line.lower() or "Your code has been rated at" in line:
                # Extract score like "7.45/10"
                import re
                match = re.search(r"(\d+\.?\d*)/10", line)
                if match:
                    return {
                        "score": float(match.group(1)),
                        "max_score": 10.0,
                    }
        
        return {
            "score": None,
            "max_score": 10.0,
            "error": "Could not parse pylint score",
        }
    except subprocess.TimeoutExpired:
        return {
            "score": None,
            "max_score": 10.0,
            "error": "Pylint timeout",
        }
    except FileNotFoundError:
        return {
            "score": None,
            "max_score": 10.0,
            "error": "pylint not found",
        }
    except Exception as e:
        return {
            "score": None,
            "max_score": 10.0,
            "error": str(e),
        }


def count_lines(file_path):
    """Count lines in a file."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except Exception:
        return None


def count_duplications_in_calc_score(file_path):
    """Count duplicated parsing patterns in calc_score function only (not in helper functions)."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Find the calc_score function
        import re
        # Match calc_score function definition and its body
        calc_score_match = re.search(r'def calc_score\([^)]*\):.*?(?=\n\ndef |\nclass |\Z)', content, re.DOTALL)
        
        if not calc_score_match:
            return {"float_calls": None, "int_calls": None, "error": "Could not find calc_score function"}
        
        calc_score_body = calc_score_match.group(0)
        
        # Count float() and int() calls in calc_score function body
        # But exclude calls that are in helper function definitions within calc_score (unlikely but possible)
        float_calls = calc_score_body.count("float(")
        int_calls = calc_score_body.count("int(")
        
        # Count calls specifically in the event loop (the duplicated pattern area)
        lines = calc_score_body.split('\n')
        in_event_loop = False
        float_in_loop = 0
        int_in_loop = 0
        
        for line in lines:
            if 'for e in events' in line:
                in_event_loop = True
            if in_event_loop:
                if 'float(' in line:
                    float_in_loop += 1
                if 'int(' in line and 'weight' in line.lower():
                    int_in_loop += 1
            # Exit event loop when we hit loyalty bonus section
            if 'loyalty bonus' in line.lower() or ('bonus =' in line and '0.0' not in line):
                in_event_loop = False
        
        return {
            "float_calls_total": float_calls,
            "int_calls_total": int_calls,
            "float_calls_in_loop": float_in_loop,
            "int_calls_in_loop": int_in_loop,
        }
    except Exception as e:
        return {"float_calls": None, "int_calls": None, "error": str(e)}


def evaluate_implementation(implementation_name, file_path):
    """Evaluate a single implementation."""
    print(f"\n{'=' * 60}")
    print(f"EVALUATING: {implementation_name.upper()}")
    print(f"{'=' * 60}")
    print(f"File: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    # Run pylint
    print(f"\nRunning pylint...")
    pylint_result = run_pylint(file_path)
    
    if pylint_result.get("score") is not None:
        print(f"Pylint score: {pylint_result['score']:.2f}/10")
    else:
        print(f"⚠️  Could not get pylint score: {pylint_result.get('error', 'Unknown error')}")
    
    # Count lines
    lines = count_lines(file_path)
    if lines is not None:
        print(f"Line count: {lines}")
    
    # Count duplications in calc_score function (not in helper functions)
    dup_info = count_duplications_in_calc_score(file_path)
    
    float_calls_in_loop = dup_info.get("float_calls_in_loop")
    int_calls_in_loop = dup_info.get("int_calls_in_loop")
    
    if float_calls_in_loop is not None:
        print(f"float() calls in event loop (duplication): {float_calls_in_loop}")
    if int_calls_in_loop is not None:
        print(f"int() calls in event loop for weight (duplication): {int_calls_in_loop}")
    
    return {
        "file_path": file_path,
        "pylint": pylint_result,
        "lines": lines,
        "float_calls_in_loop": float_calls_in_loop,
        "int_calls_in_loop": int_calls_in_loop,
        "duplication_info": dup_info,
    }


def run_evaluation(params):
    """
    Run complete evaluation for both implementations and collect metrics.
    
    Returns dict with metrics from both before and after implementations.
    """
    print(f"\n{'=' * 60}")
    print("MECHANICAL REFACTOR EVALUATION")
    print(f"{'=' * 60}")
    
    project_root = Path(__file__).parent.parent
    before_path = project_root / "repository_before" / "app" / "score.py"
    after_path = project_root / "repository_after" / "app" / "score.py"
    
    # Evaluate before implementation
    before_metrics = evaluate_implementation("before", str(before_path))
    
    # Evaluate after implementation
    after_metrics = evaluate_implementation("after", str(after_path))
    
    if not before_metrics or not after_metrics:
        print("\n❌ Evaluation failed - could not evaluate one or both implementations")
        return None
    
    # Calculate improvements
    before_score = before_metrics.get("pylint", {}).get("score")
    after_score = after_metrics.get("pylint", {}).get("score")
    
    score_improvement = None
    score_improvement_pct = None
    if before_score is not None and after_score is not None:
        score_improvement = after_score - before_score
        score_improvement_pct = (score_improvement / before_score) * 100 if before_score > 0 else 0
    
    line_change = None
    if before_metrics.get("lines") is not None and after_metrics.get("lines") is not None:
        line_change = after_metrics["lines"] - before_metrics["lines"]
    
    float_reduction = None
    if before_metrics.get("float_calls_in_loop") is not None and after_metrics.get("float_calls_in_loop") is not None:
        float_reduction = before_metrics["float_calls_in_loop"] - after_metrics["float_calls_in_loop"]
    
    int_reduction = None
    if before_metrics.get("int_calls_in_loop") is not None and after_metrics.get("int_calls_in_loop") is not None:
        int_reduction = before_metrics["int_calls_in_loop"] - after_metrics["int_calls_in_loop"]
    
    # Compile results
    metrics = {
        "before": before_metrics,
        "after": after_metrics,
        "comparison": {
            "pylint_score_improvement": round(score_improvement, 2) if score_improvement is not None else None,
            "pylint_score_improvement_pct": round(score_improvement_pct, 1) if score_improvement_pct is not None else None,
            "line_change": line_change,
            "float_calls_reduction": float_reduction,
            "int_calls_reduction": int_reduction,
        },
    }
    
    # Print summary
    print(f"\n{'=' * 60}")
    print("EVALUATION SUMMARY")
    print(f"{'=' * 60}")
    
    if before_score is not None and after_score is not None:
        print(f"\nPylint Score:")
        print(f"  Before: {before_score:.2f}/10")
        print(f"  After:  {after_score:.2f}/10")
        if score_improvement is not None:
            print(f"  Improvement: {score_improvement:+.2f} ({score_improvement_pct:+.1f}%)")
    
    if line_change is not None:
        print(f"\nLine Count:")
        print(f"  Before: {before_metrics['lines']}")
        print(f"  After:  {after_metrics['lines']}")
        print(f"  Change: {line_change:+d}")
    
    if float_reduction is not None:
        print(f"\nCode Duplication Reduction (float calls in event loop):")
        print(f"  Before: {before_metrics['float_calls_in_loop']} (duplicated in calc_score)")
        print(f"  After:  {after_metrics['float_calls_in_loop']} (should be 0 if extracted to helper)")
        print(f"  Reduction: {float_reduction:+d}")
        if float_reduction > 0:
            print(f"  ✅ Duplication reduced!")
        elif float_reduction == 0:
            print(f"  ⚠️  No reduction in duplication")
    
    if int_reduction is not None:
        print(f"\nCode Duplication Reduction (int calls for weight parsing):")
        print(f"  Before: {before_metrics['int_calls_in_loop']} (duplicated in calc_score)")
        print(f"  After:  {after_metrics['int_calls_in_loop']} (should be 0 if extracted to helper)")
        print(f"  Reduction: {int_reduction:+d}")
        if int_reduction > 0:
            print(f"  ✅ Duplication reduced!")
        elif int_reduction == 0:
            print(f"  ⚠️  No reduction in duplication")
    
    if score_improvement is not None and score_improvement > 0:
        print(f"\n✅ Code quality improved!")
    elif score_improvement is not None and score_improvement < 0:
        print(f"\n⚠️  Code quality decreased")
    
    return metrics


def main():
    """Main entry point for evaluation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run mechanical refactor evaluation")
    parser.add_argument("--output", type=str, default="evaluation/report.json", help="Output JSON file path (default: evaluation/report.json)")
    
    args = parser.parse_args()
    
    params = {}  # No parameters needed for this evaluation
    
    started_at = datetime.now()
    
    try:
        metrics = run_evaluation(params)
        success = metrics is not None
        error_message = None if success else "Evaluation failed"
    except Exception as e:
        import traceback
        print(f"\nERROR: {str(e)}")
        traceback.print_exc()
        metrics = None
        success = False
        error_message = str(e)
    
    finished_at = datetime.now()
    duration = (finished_at - started_at).total_seconds()
    
    # Build report
    report = {
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "duration_seconds": duration,
        "success": success,
        "error": error_message,
        "parameters": params,
        "metrics": metrics,
    }
    
    # Output JSON to file (default: evaluation/report.json)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Report saved to: {output_path}")
    
    print(f"\n{'=' * 60}")
    print(f"EVALUATION COMPLETE")
    print(f"{'=' * 60}")
    print(f"Duration: {duration:.2f}s")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

