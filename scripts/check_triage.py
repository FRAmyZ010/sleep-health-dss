"""Smoke checks for pre-screen rules and decision-layer conflict logic.

Mirrors the rules in web/app.js so a broken threshold or conflict path fails
before the live demo.
"""

from __future__ import annotations

import sys
from typing import Any


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


def blank_answers() -> dict[int, Any]:
    return {item: False for item in range(1, 14)}


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
    unknown_count = sum(1 for value in answers.values() if value == "unknown")
    return {
        "flagged": flagged,
        "deep_eligible": bool(flagged),
        "top_class": SCREEN_CLASS[flagged[0]["id"]] if flagged else "None",
        "unknown_count": unknown_count,
    }


def confidence_band(probability: float) -> str:
    if probability < 0.40:
        return "low"
    if probability < 0.70:
        return "mid"
    return "high"


def decide(label: str, top_probability: float, triage: dict[str, Any]) -> dict[str, Any]:
    band = confidence_band(top_probability)
    screen_class = triage["top_class"] if triage.get("deep_eligible") else "None"
    conflict = None
    risk = {"None": "Low", "Insomnia": "Medium", "Sleep Apnea": "High"}[label]

    if triage.get("deep_eligible") and screen_class != "None":
        if label == "None":
            conflict = "screen_positive_model_none"
            risk = "High"
        elif label != screen_class:
            conflict = "screen_model_mismatch"
            risk = "High"

    if conflict is None and band == "low":
        risk = "High" if label == "Sleep Apnea" else "Medium"

    return {
        "conflict": conflict,
        "risk_level": risk,
        "confidence_band": band,
        "screen_class": screen_class,
    }


def expect(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def main() -> int:
    failures: list[str] = []

    snore_only = blank_answers()
    snore_only[2] = True
    triage = evaluate_screening(snore_only)
    expect(not triage["deep_eligible"], "single snore must not unlock deep assess", failures)

    red = blank_answers()
    red[3] = True
    triage = evaluate_screening(red)
    expect(triage["deep_eligible"], "stop-breathing red flag must unlock deep assess", failures)
    expect(triage["top_class"] == "Sleep Apnea", "red flag must map to Sleep Apnea", failures)
    expect(triage["flagged"][0]["trigger"] == "red_flag", "trigger must be red_flag", failures)

    apnea_threshold = blank_answers()
    apnea_threshold[2] = True
    apnea_threshold[5] = True
    triage = evaluate_screening(apnea_threshold)
    expect(triage["deep_eligible"], "two apnea items must unlock deep assess", failures)
    expect(triage["flagged"][0]["trigger"] == "threshold", "two items should use threshold", failures)

    insomnia_one = blank_answers()
    insomnia_one[1] = True
    triage = evaluate_screening(insomnia_one)
    expect(not triage["deep_eligible"], "one insomnia item must not flag", failures)

    insomnia_two = blank_answers()
    insomnia_two[1] = True
    insomnia_two[6] = True
    triage = evaluate_screening(insomnia_two)
    expect(triage["top_class"] == "Insomnia", "two insomnia items must flag Insomnia", failures)

    alone_unknown = blank_answers()
    alone_unknown[2] = "unknown"
    alone_unknown[3] = "unknown"
    alone_unknown[4] = "unknown"
    alone_unknown[5] = "unknown"
    triage = evaluate_screening(alone_unknown)
    expect(not triage["deep_eligible"], "unknown partner items must not unlock deep assess", failures)
    expect(triage["unknown_count"] == 4, "unknown partner answers must be counted", failures)

    alone_proxy = blank_answers()
    alone_proxy[2] = "unknown"
    alone_proxy[3] = "unknown"
    alone_proxy[4] = "unknown"
    alone_proxy[5] = "unknown"
    alone_proxy[8] = True
    alone_proxy[10] = True
    triage = evaluate_screening(alone_proxy)
    expect(triage["deep_eligible"], "alone user with two self-observable apnea items must unlock", failures)
    expect(triage["top_class"] == "Sleep Apnea", "alone proxy path must map to Sleep Apnea", failures)

    conflict = decide("None", 0.82, triage)
    expect(conflict["conflict"] == "screen_positive_model_none", "screen+/model None must conflict", failures)
    expect(conflict["risk_level"] == "High", "conflict must force High risk", failures)

    mismatch = decide("Insomnia", 0.75, evaluate_screening(red))
    expect(mismatch["conflict"] == "screen_model_mismatch", "apnea screen + insomnia model must mismatch", failures)

    uncertain = decide("None", 0.33, {"deep_eligible": False, "top_class": "None"})
    expect(uncertain["confidence_band"] == "low", "0.33 must be low confidence band", failures)
    expect(uncertain["risk_level"] == "Medium", "uncertain None must not stay Low", failures)

    clear = decide("None", 0.80, {"deep_eligible": False, "top_class": "None"})
    expect(clear["conflict"] is None, "clear None path must have no conflict", failures)
    expect(clear["risk_level"] == "Low", "clear None path must stay Low", failures)

    if failures:
        print("check_triage FAILED")
        for item in failures:
            print(f"- {item}")
        return 1

    print("check_triage OK")
    print(
        "cases: weak snore blocked, red-flag unlock, thresholds, alone unknown, "
        "alone proxy, conflict, mismatch, confidence bands"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
