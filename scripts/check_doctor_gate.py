"""Easy check: proxy GT (main data) vs questionnaire / see-doctor gates."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ground_truth import evaluate_doctor_gate  # noqa: E402


def _pct(rate: float | None) -> str:
    if rate is None:
        return "—"
    return f"{100.0 * rate:.1f}%"


def _print_block(title: str, stats: dict) -> None:
    print(title)
    print(
        f"  n={stats['total']}  agree={stats['agree']} ({_pct(stats['agreement_rate'])})  "
        f"precision={_pct(stats['precision'])}  recall={_pct(stats['recall'])}  "
        f"f1={_pct(stats['f1'])}"
    )
    print(
        f"  confusion: TP={stats['tp']} FP={stats['fp']} TN={stats['tn']} FN={stats['fn']}"
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    report = evaluate_doctor_gate()
    print("=== Doctor-gate check (easy summary) ===")
    print(report["note"])
    print()
    print("Definitions")
    for key, text in report["definition"].items():
        print(f"  - {key}: {text}")
    print()
    _print_block(
        "[A] Main data GT vs model disorder flag (Kaggle labels vs pred != None)",
        report["kaggle_vs_model_disorder"],
    )
    print()
    _print_block(
        "[B] Main data GT vs clinical see-doctor gate (High/conflict; no questionnaire on Kaggle rows)",
        report["kaggle_vs_clinical_gate"],
    )
    print()
    _print_block(
        "[C] Questionnaire triage flag vs expected GT (reference profiles)",
        report["questionnaire_screen_vs_gt"],
    )
    print()
    _print_block(
        "[D] Questionnaire + model decision vs expected GT (deep profiles only)",
        report["questionnaire_full_vs_gt"],
    )

    out_dir = ROOT / "artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "doctor_gate_report.json"
    # Keep JSON lighter for slides: drop huge row dumps from the summary file? Keep them for Sheets.
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    kaggle_csv = out_dir / "doctor_gate_kaggle.csv"
    quest_csv = out_dir / "doctor_gate_questionnaire.csv"
    _write_csv(kaggle_csv, report["kaggle_rows"])
    _write_csv(quest_csv, report["questionnaire_rows"])

    print()
    print("Files for the professor / slides:")
    print(f"  {json_path.relative_to(ROOT)}")
    print(f"  {kaggle_csv.relative_to(ROOT)}")
    print(f"  {quest_csv.relative_to(ROOT)}")
    print()
    print("Quick read: higher agreement/recall is better for catching GT-positive cases.")
    print("Also open #trust → Doctor-gate section after restarting the server.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
