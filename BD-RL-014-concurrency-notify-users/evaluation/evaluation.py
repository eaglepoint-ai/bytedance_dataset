import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
BEFORE = ROOT / "repository_before" / "notify_service.py"
AFTER = ROOT / "repository_after" / "notify_service.py"


def main() -> None:
    before_src = BEFORE.read_text(encoding="utf-8")
    after_src = AFTER.read_text(encoding="utf-8")

    results = {
        "before_lines": len(before_src.splitlines()),
        "after_lines": len(after_src.splitlines()),
        "before_uses_threadpool": "ThreadPoolExecutor" in before_src,
        "after_uses_threadpool": "ThreadPoolExecutor" in after_src,
        "after_uses_MAX_WORKERS_50": "MAX_WORKERS = 50" in after_src,
        "after_streams_work": "FIRST_COMPLETED" in after_src,
    }

    out_path = ROOT / "evaluation" / "results.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
