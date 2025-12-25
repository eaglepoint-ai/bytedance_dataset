import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BEFORE = ROOT / "repository_before" / "subscription_manager.py"
AFTER = ROOT / "repository_after" / "subscription_manager.py"


def main() -> None:
    before_src = BEFORE.read_text(encoding="utf-8")
    after_src = AFTER.read_text(encoding="utf-8")

    results = {
        "before_lines": len(before_src.splitlines()),
        "after_lines": len(after_src.splitlines()),
        "before_has_pricecalculator": "PriceCalculator" in before_src,
        "after_has_pricecalculator": "PriceCalculator" in after_src,
        "after_supports_clock_injection": "clock:" in after_src or "Clock" in after_src,
        "after_has_effective_tier_logic": "_effective_tier" in after_src,
    }

    out_path = ROOT / "evaluation" / "results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
