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
        print(f"pylint repository_before/ids.py > {pylint_before_path}")
        print(f"pylint repository_after/ids.py > {pylint_after_path}")
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
                # Pylint output format: "Your code has been rated at X.XX/10"
                if "rated at" in before_pylint and "rated at" in after_pylint:
                    before_score = float(before_pylint.split("rated at")[1].split("/")[0].strip())
                    after_score = float(after_pylint.split("rated at")[1].split("/")[0].strip())
                    improvement = ((after_score - before_score) / before_score) * 100 if before_score > 0 else 0
                    print(f"Improvement: {improvement:+.1f}%")
                else:
                    # Try simple X/Y format
                    before_score = float(before_pylint.split('/')[-1])
                    after_score = float(after_pylint.split('/')[-1])
                    improvement = ((after_score - before_score) / before_score) * 100
                    print(f"Improvement: {improvement:+.1f}%")
            except (ValueError, ZeroDivisionError, IndexError):
                print("Could not parse numeric scores from pylint output")
    
    # Radon complexity
    print("\nCOMPLEXITY METRICS")
    print("-" * 60)
    
    if not os.path.exists(radon_before_path) or not os.path.exists(radon_after_path):
        print("Radon report files not found. Run radon analysis first:")
        print(f"radon cc -j repository_before/ids.py > {radon_before_path}")
        print(f"radon cc -j repository_after/ids.py > {radon_after_path}")
    else:
        try:
            with open(radon_before_path) as f:
                before_radon = json.load(f)
            with open(radon_after_path) as f:
                after_radon = json.load(f)
            
            if before_radon and after_radon:
                # Radon returns a dict with filename as key
                before_data = list(before_radon.values())[0] if before_radon else []
                after_data = list(after_radon.values())[0] if after_radon else []
                
                if before_data and after_data:
                    # Compare complexity of main function
                    before_main = [f for f in before_data if f.get('name') == 'normalize_id']
                    after_main = [f for f in after_data if f.get('name') == 'normalize_id']
                    
                    if before_main and after_main:
                        before_complexity = before_main[0].get('complexity', 0)
                        after_complexity = after_main[0].get('complexity', 0)
                        
                        print(f"normalize_id complexity:")
                        print(f"  Before: {before_complexity}")
                        print(f"  After:  {after_complexity}")
                        
                        if before_complexity > 0:
                            improvement = ((before_complexity - after_complexity) / before_complexity) * 100
                            print(f"  Reduction: {improvement:.1f}%")
                    
                    # Show all functions
                    print("\nAll functions (Before):")
                    for func in before_data:
                        print(f"  - {func.get('name', 'unknown')}: complexity={func.get('complexity', 0)}")
                    
                    print("\nAll functions (After):")
                    for func in after_data:
                        print(f"  - {func.get('name', 'unknown')}: complexity={func.get('complexity', 0)}")
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
