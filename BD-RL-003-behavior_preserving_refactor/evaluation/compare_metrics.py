"""Compare quality metrics between before and after versions."""
import json
import sys
import os


def compare_metrics():
    """Load and compare all metrics."""
    print("=" * 60)
    print("CODE QUALITY COMPARISON")
    print("=" * 60)
    
    # Check if metric files exist and have content
    pylint_before_path = 'evaluation/pylint_score_before.txt'
    pylint_after_path = 'evaluation/pylint_score_after.txt'
    radon_before_path = 'evaluation/radon_report_before.json'
    radon_after_path = 'evaluation/radon_report_after.json'
    
    # Pylint scores
    print("\nPYLINT SCORES")
    print("-" * 60)
    
    if not os.path.exists(pylint_before_path) or not os.path.exists(pylint_after_path):
        print("Pylint score files not found. Run pylint analysis first:")
        print(f"pylint repository_before/calc_total.py > {pylint_before_path}")
        print(f"pylint repository_after/calc_total.py > {pylint_after_path}")
    else:
        with open(pylint_before_path) as f:
            before_pylint = f.read().strip()
        with open(pylint_after_path) as f:
            after_pylint = f.read().strip()
        
        if not before_pylint or not after_pylint:
            print("Pylint score files are empty. Run pylint analysis first.")
        else:
            print(f"Before: {before_pylint}")
            print(f"After:  {after_pylint}")
            
            # Try to extract numeric scores
            try:
                before_score = float(before_pylint.split('/')[-1])
                after_score = float(after_pylint.split('/')[-1])
                improvement = ((after_score - before_score) / before_score) * 100
                print(f"Improvement: {improvement:+.1f}%")
            except (ValueError, ZeroDivisionError):
                print("Could not parse numeric scores from pylint output")
    
    # Radon complexity
    print("\nCOMPLEXITY METRICS")
    print("-" * 60)
    
    if not os.path.exists(radon_before_path) or not os.path.exists(radon_after_path):
        print("Radon report files not found. Run radon analysis first:")
        print(f"   radon cc -j repository_before/calc_total.py > {radon_before_path}")
        print(f"   radon cc -j repository_after/calc_total.py > {radon_after_path}")
    else:
        try:
            with open(radon_before_path) as f:
                before_radon = json.load(f)
            with open(radon_after_path) as f:
                after_radon = json.load(f)
            
            if before_radon and after_radon and len(before_radon) > 0 and len(after_radon) > 0:
                for key in before_radon[0]:
                    if key in ['complexity', 'mi']:
                        before_val = before_radon[0][key]
                        after_val = after_radon[0][key]
                        print(f"{key.upper():15} Before: {before_val:6.2f} | After: {after_val:6.2f}")
            else:
                print("Radon report files are empty or invalid")
        except (json.JSONDecodeError, KeyError, IndexError) as e:
            print(f"Could not parse radon reports: {e}")
    
    print("\n" + "=" * 60)
    print("Tests validate behavior preservation")
    print("Metrics above show quality improvements (if available)")
    print("=" * 60)


if __name__ == '__main__':
    compare_metrics()