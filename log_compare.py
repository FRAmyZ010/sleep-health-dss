"""Enrich anonymous assessment logs with rule GT and Kaggle proxy GT."""

from __future__ import annotations

from collections import Counter
from typing import Any

from ground_truth import evaluate_screening
from model import FEATURES, TARGET, get_bundle

# Numeric class codes for Sheets / charts: easy to average and compare.
CLASS_CODE = {"None": 0, "Insomnia": 1, "Sleep Apnea": 2}


def class_to_code(label: Any) -> int | None:
    if label is None or label == "":
        return None
    return CLASS_CODE.get(str(label), None)


def bool_to_num(value: Any) -> int | None:
    if value is None:
        return None
    return 1 if bool(value) else 0


def _answers_int_keys(raw: Any) -> dict[int, Any]:
    answers = {item: False for item in range(1, 14)}
    if not isinstance(raw, dict):
        return answers
    for key, value in raw.items():
        try:
            qid = int(key)
        except (TypeError, ValueError):
            continue
        if qid in answers:
            answers[qid] = value
    return answers


def rule_ground_truth(screening_answers: Any) -> dict[str, Any]:
    """Auto GT from questionnaire using the project reference triage rules."""

    answers = _answers_int_keys(screening_answers)
    triage = evaluate_screening(answers)
    label = str(triage.get("top_class") or "None")
    see_doctor = bool(triage.get("deep_eligible"))
    return {
        "gt_rule_class": label,
        "gt_rule_see_doctor": see_doctor,
        "gt_rule_source": "questionnaire_triage_rules",
        "gt_rule_triage": {
            "top_class": triage.get("top_class"),
            "deep_eligible": triage.get("deep_eligible"),
            "flagged": triage.get("flagged"),
        },
    }


def _row_age_bmi_gender(form_payload: Any, profile: Any) -> tuple[float | None, str | None, str | None]:
    age = None
    bmi = None
    gender = None
    for source in (profile, form_payload):
        if not isinstance(source, dict):
            continue
        if age is None:
            try:
                age = float(source.get("Age", source.get("age")))
            except (TypeError, ValueError):
                age = None
        if bmi is None:
            value = source.get("BMI Category") or source.get("bmi_category")
            if value:
                bmi = str(value)
        if gender is None:
            value = source.get("Gender") or source.get("gender")
            if value:
                gender = str(value)
    return age, bmi, gender


def proxy_ground_truth(
    form_payload: Any,
    profile: Any,
    *,
    age_window: float = 10.0,
    min_similar: int = 3,
    bundle: dict | None = None,
) -> dict[str, Any]:
    """Proxy GT = majority Sleep Disorder label among similar Kaggle rows."""

    bundle = bundle or get_bundle()
    frame = bundle["frame"]
    age, bmi, gender = _row_age_bmi_gender(form_payload, profile)
    matched = frame
    if gender:
        matched = matched[matched["Gender"].astype(str) == gender]
    if bmi:
        matched = matched[matched["BMI Category"].astype(str) == bmi]
    if age is not None:
        matched = matched[matched["Age"].between(float(age) - age_window, float(age) + age_window)]

    labels = matched[TARGET].astype(str).tolist() if len(matched) else []
    counts = Counter(labels)
    similar_count = len(labels)
    if similar_count >= min_similar and counts:
        proxy_label, proxy_n = counts.most_common(1)[0]
        confidence = proxy_n / similar_count
    else:
        proxy_label, proxy_n, confidence = None, 0, None

    return {
        "gt_proxy_class": proxy_label,
        "gt_proxy_see_doctor": (proxy_label is not None and proxy_label != "None"),
        "gt_proxy_source": "kaggle_similar_majority",
        "gt_proxy_similar_count": similar_count,
        "gt_proxy_vote_count": proxy_n,
        "gt_proxy_confidence": confidence,
        "gt_proxy_match": {
            "age": age,
            "age_window": age_window,
            "bmi_category": bmi,
            "gender": gender,
            "min_similar": min_similar,
        },
        "gt_proxy_eligible": similar_count >= min_similar and proxy_label is not None,
    }


def flatten_questionnaire(screening_answers: Any) -> dict[str, Any]:
    answers = _answers_int_keys(screening_answers)
    flat: dict[str, Any] = {}
    yes_count = 0
    for qid in range(1, 14):
        value = answers.get(qid)
        if value is True:
            flat[f"q{qid}"] = "yes"
            flat[f"q{qid}_num"] = 1
            yes_count += 1
        elif value is False:
            flat[f"q{qid}"] = "no"
            flat[f"q{qid}_num"] = 0
        elif value == "unknown":
            flat[f"q{qid}"] = "unknown"
            flat[f"q{qid}_num"] = -1
        else:
            flat[f"q{qid}"] = ""
            flat[f"q{qid}_num"] = ""
    flat["questionnaire_yes_score"] = yes_count
    flat["questionnaire_yes_rate"] = round(yes_count / 13.0, 4)
    return flat


def explain_scores(row: dict[str, Any], rule: dict[str, Any], proxy: dict[str, Any], compare: dict[str, Any]) -> dict[str, Any]:
    """Human-readable + numeric reasons for sheet/demo explanations."""

    hybrid = row.get("hybrid_score")
    top_p = row.get("top_probability")
    screen_s = row.get("screen_strength")
    risk = str(row.get("risk_level") or "")
    conflict = row.get("conflict")
    model_label = str(row.get("model_label") or "None")
    screen_class = str(row.get("screen_class") or "None")
    parts: list[str] = []
    if top_p is not None:
        parts.append(f"model_top_prob={float(top_p):.3f}")
    if screen_s is not None:
        parts.append(f"screen_strength={float(screen_s):.3f}")
    if hybrid is not None:
        parts.append(f"hybrid=0.6*model+0.4*screen → {float(hybrid):.3f}")
    if conflict:
        parts.append(f"conflict={conflict} forces High / see-doctor")
    elif risk:
        parts.append(f"risk_level={risk} from decision layer")
    if compare.get("match_rule_vs_model") is False:
        parts.append(
            f"Rule GT ({rule.get('gt_rule_class')}) ≠ model ({model_label})"
        )
    if proxy.get("gt_proxy_eligible") and compare.get("match_proxy_vs_model") is False:
        parts.append(
            f"Proxy GT ({proxy.get('gt_proxy_class')}) ≠ model ({model_label}) "
            f"from {proxy.get('gt_proxy_similar_count')} similar Kaggle rows"
        )
    if not parts:
        parts.append("scores follow model probability and screen evidence")

    agree_vals = [
        compare.get("match_rule_vs_model_num"),
        compare.get("match_proxy_vs_model_num"),
        compare.get("match_rule_vs_proxy_num"),
    ]
    usable = [float(v) for v in agree_vals if v is not None]
    agreement_score = round(sum(usable) / len(usable), 4) if usable else None

    return {
        "score_why": " | ".join(parts),
        "score_why_th": (
            f"คะแนน hybrid จากความน่าจะเป็นโมเดลและหลักฐานหน้าจอ"
            f"{' · conflict บังคับพบหมอ' if conflict else ''}"
            f"{' · Rule GT ไม่ตรงโมเดล' if compare.get('match_rule_vs_model') is False else ''}"
            f"{' · Proxy GT ไม่ตรงโมเดล' if compare.get('match_proxy_vs_model') is False else ''}"
        ),
        "agreement_score": agreement_score,
        "hybrid_model_weight": 0.6,
        "hybrid_screen_weight": 0.4,
        "class_code_legend": "0=None,1=Insomnia,2=Sleep Apnea",
        "match_code_legend": "1=agree,0=disagree,blank=n/a",
        "screen_class_code": class_to_code(screen_class),
        "model_label_code": class_to_code(model_label),
        "risk_code": {"Low": 0, "Medium": 1, "High": 2}.get(risk),
    }


def compare_against_system(row: dict[str, Any], rule: dict[str, Any], proxy: dict[str, Any]) -> dict[str, Any]:
    model_label = str(row.get("model_label") or "None")
    screen_class = str(row.get("screen_class") or "None")
    risk = str(row.get("risk_level") or "")
    conflict = row.get("conflict")
    system_see_doctor = risk == "High" or bool(conflict)

    rule_class = rule.get("gt_rule_class")
    proxy_class = proxy.get("gt_proxy_class")
    match_rule_screen = rule_class == screen_class
    match_rule_model = rule_class == model_label
    match_proxy_model = (proxy_class == model_label) if proxy_class is not None else None
    match_rule_proxy = (rule_class == proxy_class) if proxy_class is not None else None
    match_doc_rule = system_see_doctor == bool(rule.get("gt_rule_see_doctor"))
    match_doc_proxy = (
        system_see_doctor == bool(proxy.get("gt_proxy_see_doctor"))
        if proxy.get("gt_proxy_eligible")
        else None
    )
    return {
        "system_see_doctor": system_see_doctor,
        "system_see_doctor_num": bool_to_num(system_see_doctor),
        "gt_rule_class_code": class_to_code(rule_class),
        "gt_rule_see_doctor_num": bool_to_num(rule.get("gt_rule_see_doctor")),
        "gt_proxy_class_code": class_to_code(proxy_class),
        "gt_proxy_see_doctor_num": bool_to_num(proxy.get("gt_proxy_see_doctor"))
        if proxy.get("gt_proxy_eligible")
        else None,
        "match_rule_vs_screen": match_rule_screen,
        "match_rule_vs_model": match_rule_model,
        "match_proxy_vs_model": match_proxy_model,
        "match_rule_vs_proxy": match_rule_proxy,
        "match_see_doctor_rule": match_doc_rule,
        "match_see_doctor_proxy": match_doc_proxy,
        "match_rule_vs_screen_num": bool_to_num(match_rule_screen),
        "match_rule_vs_model_num": bool_to_num(match_rule_model),
        "match_proxy_vs_model_num": bool_to_num(match_proxy_model),
        "match_rule_vs_proxy_num": bool_to_num(match_rule_proxy),
        "match_see_doctor_rule_num": bool_to_num(match_doc_rule),
        "match_see_doctor_proxy_num": bool_to_num(match_doc_proxy),
    }


def enrich_assessment_row(row: dict[str, Any], bundle: dict | None = None) -> dict[str, Any]:
    """Attach questionnaire flat fields + rule GT + Kaggle proxy GT + comparisons."""

    bundle = bundle or get_bundle()
    screening_answers = row.get("screening_answers")
    if screening_answers is None and isinstance(row.get("screening_triage"), dict):
        screening_answers = {}
    form_payload = row.get("form_payload")
    profile = row.get("profile")
    rule = rule_ground_truth(screening_answers)
    proxy = proxy_ground_truth(form_payload, profile, bundle=bundle)
    compare = compare_against_system(row, rule, proxy)
    flat = flatten_questionnaire(screening_answers)
    explain = explain_scores(row, rule, proxy, compare)
    enriched = dict(row)
    enriched.update(flat)
    enriched.update(rule)
    enriched.update(proxy)
    enriched.update(compare)
    enriched.update(explain)
    # Keep payload size reasonable for list endpoints.
    if "gt_rule_triage" in enriched and not row.get("_keep_triage_detail"):
        enriched["gt_rule_flagged_count"] = len((rule.get("gt_rule_triage") or {}).get("flagged") or [])
    return enriched


def enrich_assessment_rows(rows: list[dict[str, Any]], bundle: dict | None = None) -> list[dict[str, Any]]:
    bundle = bundle or get_bundle()
    return [enrich_assessment_row(row, bundle=bundle) for row in rows]
