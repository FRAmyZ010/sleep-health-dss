"""Report proxy (Kaggle CV) and reference-profile ground-truth checks."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ground_truth import build_trust_report  # noqa: E402


def _pct(rate: float | None) -> str:
    if rate is None:
        return "—"
    return f"{100.0 * rate:.1f}%"


def main() -> int:
    report = build_trust_report()
    proxy = report["kaggle_proxy"]
    spot = report["in_sample_spotcheck"]
    reference = report["reference_profiles"]

    print("=== Ground-truth trust report ===")
    print(report["disclaimer"])
    print()
    print("[1] Kaggle proxy GT (stratified CV)")
    print(f"  rows={proxy['row_count']} folds={proxy['folds']}")
    print(
        "  accuracy="
        f"{proxy['accuracy']['mean']:.3f}±{proxy['accuracy']['std']:.3f} "
        f"macro_f1={proxy['f1_macro']['mean']:.3f}±{proxy['f1_macro']['std']:.3f}"
    )
    print(f"  class_counts={proxy['class_counts']}")
    print(f"  observed_age_range={proxy['observed_age_range']}")
    if proxy.get("caveat"):
        print("  caveat: duplicate feature rows may inflate CV scores")
    print()
    print("[2] In-sample spot-check (optimistic)")
    print(f"  {spot['correct']}/{spot['total']} match ({_pct(spot['rate'])})")
    print(f"  note: {spot['note']}")
    print()
    print("[3] Reference profiles")
    print(f"  file: {reference['path']}")
    print(
        "  screen "
        f"{reference['screen']['correct']}/{reference['screen']['total']} "
        f"({_pct(reference['screen']['rate'])})"
    )
    print(
        "  model "
        f"{reference['model']['correct']}/{reference['model']['total']} "
        f"({_pct(reference['model']['rate'])})"
    )
    mismatches = [
        row
        for row in reference["rows"]
        if row.get("screen_match") is False or row.get("model_match") is False
    ]
    if mismatches:
        print("  mismatches:")
        for row in mismatches:
            bits = [row["id"]]
            if row.get("screen_match") is False:
                bits.append(
                    f"screen {row.get('predicted_screen_class')}!={row.get('expected_screen_class')}"
                )
            if row.get("model_match") is False:
                bits.append(
                    f"model {row.get('predicted_label')}!={row.get('expected_label')}"
                )
            print("   - " + " | ".join(bits))
    else:
        print("  all reference checks matched expected labels")

    # Machine-readable dump for reports
    out_path = ROOT / "artifacts" / "ground_truth_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print(f"Wrote {out_path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
