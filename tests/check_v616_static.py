"""v61.6-stable static checks for the active dashboard bundle."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE_JSX = ROOT / "js" / "app.jsx"
ACTIVE_HTML = ROOT / "index.html"

FORBIDDEN_JSX = [
    "Math.random",
    "mockData",
    "66.8",
    "1327",
    "103.8",
    "4.72",
    "16.5",
    "top_valid",
    "currentMeta",
]


def main() -> int:
    jsx = ACTIVE_JSX.read_text(encoding="utf-8")
    html = ACTIVE_HTML.read_text(encoding="utf-8")

    failures = []
    for token in FORBIDDEN_JSX:
        if token in jsx:
            failures.append(f"{ACTIVE_JSX.relative_to(ROOT)} contains {token}")

    for legacy in ["js/app.js", "js/regime.js", "js/retrain.js"]:
        if f'src="{legacy}"' in html:
            failures.append(f"{ACTIVE_HTML.relative_to(ROOT)} still loads {legacy}")

    required = [
        "factor_snapshots",
        "performance_tracking",
        "performance_snapshots",
        "meta_summaries",
        "weeklyPicks",
        "data_status",
        "fallback_used",
        "synthetic_data_used",
    ]
    for token in required:
        if token not in jsx:
            failures.append(f"{ACTIVE_JSX.relative_to(ROOT)} missing {token}")

    if failures:
        print("STATIC_CHECK_FAIL")
        for item in failures:
            print(f"- {item}")
        return 1

    print("STATIC_CHECK_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
