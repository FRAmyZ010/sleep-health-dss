"""Proxy and reference ground-truth helpers for the course demo.

Proxy ground truth = Kaggle `Sleep Disorder` labels via stratified CV metrics.
Reference ground truth = curated profiles in data/ground_truth_profiles.json.
Neither replaces a clinician diagnosis.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from model import CLASS_ORDER, FEATURES, TARGET, get_bundle, predict_record

ROOT = Path(__file__).resolve().parent
PROFILES_PATH = ROOT / "data" / "ground_truth_profiles.json"

# Mirror of web/app.js screening rules for reference screen checks.
SCREENING_GROUPS = [
    {
        "id": "insomnia",
        "questions": [1, 6, 9],
        "min_hits": 2,
        "red_flags": [],
        "severity": 3,
    },
    {
        "id": "sleep_apnea",
        "questions": [2, 3, 4, 5, 7, 8, 10, 11, 12, 13],
        "min_hits": 2,
        "red_flags": [3, 4, 12],
        "severity": 5,
    },
]
SCREEN_CLASS = {"insomnia": "Insomnia", "sleep_apnea": "Sleep Apnea"}


def load_reference_profiles(path: Path = PROFILES_PATH) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("profiles"), list):
        raise ValueError("invalid_ground_truth_profiles")
    return payload


def evaluate_screening(answers: dict[int, Any]) -> dict[str, Any]:
    flagged: list[dict[str, Any]] = []
    for group in SCREENING_GROUPS:
        hits = [qid for qid in group["questions"] if answers.get(qid) is True]
        red_hits = [qid for qid in group["red_flags"] if answers.get(qid) is True]
        by_threshold = len(hits) >= group["min_hits"]
        by_red = bool(red_hits)
        if not (by_threshold or by_red):
            continue
        flagged.append(
            {
                "id": group["id"],
                "hit_count": len(hits),
                "min_hits": group["min_hits"],
                "severity": group["severity"],
                "trigger": "red_flag" if by_red else "threshold",
                "red_hits": red_hits,
            }
        )
    flagged.sort(key=lambda row: (-row["hit_count"], -row["severity"]))
    return {
        "flagged": flagged,
        "deep_eligible": bool(flagged),
        "top_class": SCREEN_CLASS[flagged[0]["id"]] if flagged else "None",
    }


def _answers_from_profile(profile: dict[str, Any]) -> dict[int, Any]:
    answers = {item: False for item in range(1, 14)}
    for qid in profile.get("screening_yes") or []:
        answers[int(qid)] = True
    for qid in profile.get("screening_unknown") or []:
        answers[int(qid)] = "unknown"
    return answers


def _pack_metric(stats: dict[str, float]) -> dict[str, float]:
    return {
        "mean": float(stats["mean"]),
        "std": float(stats["std"]),
    }


def kaggle_proxy_summary(bundle: dict | None = None) -> dict[str, Any]:
    """Stratified CV metrics against Kaggle Sleep Disorder labels (proxy GT)."""

    bundle = bundle or get_bundle()
    meta = bundle["meta"]
    metrics = meta["metrics"]
    frame = bundle["frame"]
    return {
        "kind": "kaggle_proxy",
        "label_field": TARGET,
        "note": (
            "Proxy ground truth uses public Kaggle Sleep Disorder labels under "
            "stratified cross-validation. This is not clinician-confirmed truth."
        ),
        "row_count": int(meta["row_count"]),
        "class_counts": {label: int(meta["class_counts"].get(label, 0)) for label in CLASS_ORDER},
        "folds": int(metrics["folds"]),
        "accuracy": _pack_metric(metrics["accuracy"]),
        "precision_macro": _pack_metric(metrics["precision_macro"]),
        "recall_macro": _pack_metric(metrics["recall_macro"]),
        "f1_macro": _pack_metric(metrics["f1_macro"]),
        "per_class": {
            label: {
                key: _pack_metric(metrics["per_class"][label][key])
                for key in ("precision", "recall", "f1")
            }
            for label in CLASS_ORDER
        },
        "duplicate_feature_rows": int(meta.get("duplicate_feature_rows", 0)),
        "caveat": bool(meta.get("caveat")),
        "source_path": str(meta.get("source_path", "")),
        "observed_age_range": [
            int(frame["Age"].min()),
            int(frame["Age"].max()),
        ],
    }


def in_sample_spotcheck(bundle: dict | None = None, per_class: int = 5) -> dict[str, Any]:
    """Optimistic spot-check: predict training rows and compare to Kaggle labels."""

    bundle = bundle or get_bundle()
    frame = bundle["frame"]
    pipeline = bundle["pipeline"]
    samples: list[pd.DataFrame] = []
    for label in CLASS_ORDER:
        part = frame[frame[TARGET] == label]
        if part.empty:
            continue
        take = min(per_class, len(part))
        # Deterministic slice (not random) so the spot-check is stable across runs.
        samples.append(part.sort_values(["Age", "Occupation"]).iloc[:take])
    if not samples:
        return {"kind": "in_sample_spotcheck", "total": 0, "correct": 0, "rate": None, "rows": []}
    sample = pd.concat(samples, ignore_index=True)
    predicted = list(map(str, pipeline.predict(sample[FEATURES])))
    rows = []
    correct = 0
    for i, (_, row) in enumerate(sample.iterrows()):
        pred = predicted[i]
        truth = str(row[TARGET])
        match = pred == truth
        correct += int(match)
        rows.append(
            {
                "expected_label": truth,
                "predicted_label": pred,
                "match": match,
                "Age": int(row["Age"]),
                "Gender": str(row["Gender"]),
                "Occupation": str(row["Occupation"]),
                "BMI Category": str(row["BMI Category"]),
            }
        )
    total = len(rows)
    return {
        "kind": "in_sample_spotcheck",
        "note": (
            "Optimistic spot-check on training rows already seen by the fitted "
            "pipeline. Prefer stratified CV for proxy ground-truth claims."
        ),
        "total": total,
        "correct": correct,
        "rate": (correct / total) if total else None,
        "rows": rows,
    }


def evaluate_reference_profiles(bundle: dict | None = None) -> dict[str, Any]:
    """Score curated reference profiles for screen and/or model agreement."""

    bundle = bundle or get_bundle()
    catalog = load_reference_profiles()
    rows: list[dict[str, Any]] = []
    screen_total = screen_correct = 0
    model_total = model_correct = 0

    for profile in catalog["profiles"]:
        item: dict[str, Any] = {
            "id": profile.get("id"),
            "kind": profile.get("kind"),
            "title": profile.get("title"),
            "rationale": profile.get("rationale"),
        }
        answers = _answers_from_profile(profile)
        triage = evaluate_screening(answers)
        expected_screen = profile.get("expected_screen_class")
        if expected_screen is not None:
            screen_total += 1
            screen_match = triage["top_class"] == expected_screen
            screen_correct += int(screen_match)
            item["expected_screen_class"] = expected_screen
            item["predicted_screen_class"] = triage["top_class"]
            item["screen_match"] = screen_match

        if profile.get("kind") == "deep_assess" and profile.get("form"):
            expected_label = profile.get("expected_label")
            result = predict_record(bundle, profile["form"])
            predicted = result["label"]
            item["expected_label"] = expected_label
            item["predicted_label"] = predicted
            item["probabilities"] = result["probabilities"]
            if expected_label is not None:
                model_total += 1
                model_match = predicted == expected_label
                model_correct += int(model_match)
                item["model_match"] = model_match
        rows.append(item)

    return {
        "kind": "reference_profiles",
        "version": catalog.get("version"),
        "disclaimer": catalog.get("disclaimer"),
        "path": str(PROFILES_PATH.relative_to(ROOT)).replace("\\", "/"),
        "screen": {
            "total": screen_total,
            "correct": screen_correct,
            "rate": (screen_correct / screen_total) if screen_total else None,
        },
        "model": {
            "total": model_total,
            "correct": model_correct,
            "rate": (model_correct / model_total) if model_total else None,
        },
        "rows": rows,
    }


def _is_disorder(label: str | None) -> bool:
    return str(label or "None") != "None"


def _binary_rates(pairs: list[tuple[bool, bool]]) -> dict[str, Any]:
    """pairs = (gt_see_doctor, system_see_doctor)."""

    total = len(pairs)
    if not total:
        return {
            "total": 0,
            "agree": 0,
            "agreement_rate": None,
            "tp": 0,
            "fp": 0,
            "tn": 0,
            "fn": 0,
            "precision": None,
            "recall": None,
            "f1": None,
        }
    tp = sum(1 for gt, sys in pairs if gt and sys)
    fp = sum(1 for gt, sys in pairs if (not gt) and sys)
    tn = sum(1 for gt, sys in pairs if (not gt) and (not sys))
    fn = sum(1 for gt, sys in pairs if gt and (not sys))
    agree = tp + tn
    precision = (tp / (tp + fp)) if (tp + fp) else None
    recall = (tp / (tp + fn)) if (tp + fn) else None
    f1 = (
        (2 * precision * recall / (precision + recall))
        if precision is not None and recall is not None and (precision + recall)
        else None
    )
    return {
        "total": total,
        "agree": agree,
        "agreement_rate": agree / total,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


def mirror_decision_see_doctor(
    label: str,
    probabilities: dict[str, float],
    triage: dict[str, Any] | None,
) -> dict[str, Any]:
    """Approximate the web decision-layer 'see a clinician' gate (without log prior)."""

    top_prob = float(probabilities.get(label, 0.0) or 0.0)
    triage = triage or {"deep_eligible": False, "top_class": "None"}
    screen_class = triage["top_class"] if triage.get("deep_eligible") else "None"
    conflict = None
    if triage.get("deep_eligible") and screen_class != "None":
        if label == "None":
            conflict = "screen_positive_model_none"
        elif label != screen_class:
            conflict = "screen_model_mismatch"

    if conflict:
        return {
            "see_doctor": True,
            "risk_level": "High",
            "conflict": conflict,
            "reason": "conflict",
        }

    if top_prob < 0.40:
        risk = "High" if label == "Sleep Apnea" else "Medium"
    elif top_prob < 0.70:
        risk = "Low" if label == "None" else ("High" if label == "Sleep Apnea" else "Medium")
    else:
        risk = {"None": "Low", "Insomnia": "Medium", "Sleep Apnea": "High"}.get(label, "Medium")

    # Strong screen evidence can raise Medium → High when stages agree.
    if screen_class == label and screen_class != "None":
        flagged = triage.get("flagged") or []
        top = flagged[0] if flagged else None
        strength = 0.0
        red = False
        if top:
            total = max(int(top.get("total") or top.get("min_hits") or 1), 1)
            hits = int(top.get("hit_count") or top.get("hitCount") or 0)
            strength = hits / total
            red = top.get("trigger") == "red_flag"
            if red:
                strength = max(0.85, strength)
        if red or strength >= 0.5:
            if risk == "Medium":
                risk = "High"

    see = risk == "High" or conflict is not None
    return {
        "see_doctor": see,
        "risk_level": risk,
        "conflict": conflict,
        "reason": "high_risk" if see else "not_high",
    }


def evaluate_doctor_gate(bundle: dict | None = None) -> dict[str, Any]:
    """Compare proxy GT (main Kaggle labels) vs questionnaire / decision gates."""

    bundle = bundle or get_bundle()
    frame = bundle["frame"]
    pipeline = bundle["pipeline"]
    feature_table = frame[FEATURES]
    predicted = list(map(str, pipeline.predict(feature_table)))
    actual = frame[TARGET].astype(str).tolist()
    classes = list(pipeline.named_steps["model"].classes_)
    proba_matrix = pipeline.predict_proba(feature_table)

    kaggle_disorder_pairs: list[tuple[bool, bool]] = []
    kaggle_clinical_pairs: list[tuple[bool, bool]] = []
    kaggle_rows: list[dict[str, Any]] = []
    for i, _row in enumerate(frame.itertuples(index=False)):
        gt_label = actual[i]
        pred_label = predicted[i]
        gt = _is_disorder(gt_label)
        disorder_sys = _is_disorder(pred_label)
        # No questionnaire on Kaggle rows: decision uses model path only.
        probs = {label: 0.0 for label in CLASS_ORDER}
        probs.update({str(c): float(p) for c, p in zip(classes, proba_matrix[i])})
        clinical = mirror_decision_see_doctor(pred_label, probs, triage=None)
        kaggle_disorder_pairs.append((gt, disorder_sys))
        kaggle_clinical_pairs.append((gt, bool(clinical["see_doctor"])))
        kaggle_rows.append(
            {
                "source": "kaggle",
                "gt_label": gt_label,
                "gt_see_doctor": gt,
                "model_label": pred_label,
                "system_disorder_flag": disorder_sys,
                "system_see_doctor": bool(clinical["see_doctor"]),
                "risk_level": clinical["risk_level"],
                "agree_disorder": gt == disorder_sys,
                "agree_clinical": gt == bool(clinical["see_doctor"]),
            }
        )

    catalog = load_reference_profiles()
    screen_pairs: list[tuple[bool, bool]] = []
    full_pairs: list[tuple[bool, bool]] = []
    questionnaire_rows: list[dict[str, Any]] = []
    for profile in catalog["profiles"]:
        expected_label = profile.get("expected_label") or profile.get("expected_screen_class") or "None"
        gt = _is_disorder(str(expected_label))
        answers = _answers_from_profile(profile)
        triage = evaluate_screening(answers)
        screen_sys = bool(triage.get("deep_eligible"))
        screen_pairs.append((gt, screen_sys))
        row: dict[str, Any] = {
            "source": "questionnaire_profile",
            "id": profile.get("id"),
            "kind": profile.get("kind"),
            "gt_label": expected_label,
            "gt_see_doctor": gt,
            "screen_class": triage.get("top_class"),
            "system_screen_flag": screen_sys,
            "agree_screen": gt == screen_sys,
        }
        if profile.get("kind") == "deep_assess" and profile.get("form"):
            result = predict_record(bundle, profile["form"])
            clinical = mirror_decision_see_doctor(
                result["label"],
                result["probabilities"],
                triage,
            )
            full_pairs.append((gt, bool(clinical["see_doctor"])))
            row.update(
                {
                    "model_label": result["label"],
                    "system_see_doctor": bool(clinical["see_doctor"]),
                    "risk_level": clinical["risk_level"],
                    "conflict": clinical["conflict"],
                    "agree_clinical": gt == bool(clinical["see_doctor"]),
                }
            )
        questionnaire_rows.append(row)

    return {
        "kind": "doctor_gate",
        "definition": {
            "gt_see_doctor": "Sleep Disorder label is not None (proxy from main Kaggle data / expected profile label).",
            "system_disorder_flag": "Model class is not None.",
            "system_screen_flag": "Questionnaire triage flags Insomnia or Sleep Apnea (deep eligible).",
            "system_see_doctor": "Decision layer risk is High or conflict forces clinical review (log prior not included).",
        },
        "note": (
            "Use this to check whether 'see a clinician' gates agree with proxy ground truth. "
            "Kaggle rows have no questionnaire answers, so section A is model/decision only. "
            "Section B uses curated questionnaire profiles."
        ),
        "kaggle_vs_model_disorder": _binary_rates(kaggle_disorder_pairs),
        "kaggle_vs_clinical_gate": _binary_rates(kaggle_clinical_pairs),
        "questionnaire_screen_vs_gt": _binary_rates(screen_pairs),
        "questionnaire_full_vs_gt": _binary_rates(full_pairs),
        "kaggle_rows": kaggle_rows,
        "questionnaire_rows": questionnaire_rows,
    }


def doctor_gate_for_ui(bundle: dict | None = None) -> dict[str, Any]:
    """Compact doctor-gate payload for `#trust` (full rows stay in the CLI export)."""

    report = evaluate_doctor_gate(bundle)
    kaggle_mismatches = [row for row in report["kaggle_rows"] if not row.get("agree_clinical")]
    return {
        "kind": report["kind"],
        "definition": report["definition"],
        "note": report["note"],
        "kaggle_vs_model_disorder": report["kaggle_vs_model_disorder"],
        "kaggle_vs_clinical_gate": report["kaggle_vs_clinical_gate"],
        "questionnaire_screen_vs_gt": report["questionnaire_screen_vs_gt"],
        "questionnaire_full_vs_gt": report["questionnaire_full_vs_gt"],
        "questionnaire_rows": report["questionnaire_rows"],
        "kaggle_mismatch_count": len(kaggle_mismatches),
        "kaggle_mismatch_sample": kaggle_mismatches[:12],
        "cli_hint": "python scripts/check_doctor_gate.py",
    }


def build_trust_report(bundle: dict | None = None, spotcheck_per_class: int = 5) -> dict[str, Any]:
    bundle = bundle or get_bundle()
    return {
        "disclaimer": (
            "Ground truth in this demo has two layers: (1) Kaggle Sleep Disorder "
            "labels as proxy GT via CV, and (2) curated reference profiles. "
            "Neither is a clinical diagnosis."
        ),
        "kaggle_proxy": kaggle_proxy_summary(bundle),
        "in_sample_spotcheck": in_sample_spotcheck(bundle, per_class=spotcheck_per_class),
        "reference_profiles": evaluate_reference_profiles(bundle),
        "doctor_gate": doctor_gate_for_ui(bundle),
    }
