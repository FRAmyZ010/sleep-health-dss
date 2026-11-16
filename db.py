"""Anonymous assessment log stored in local SQLite for audit / backtrace."""

from __future__ import annotations

import csv
import io
import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "assessments.db"

# Flat columns used for list views and CSV export (Google Sheets-friendly).
EXPORT_COLUMNS = [
    "id",
    "anon_id",
    "created_at",
    "screen_class",
    "model_label",
    "risk_level",
    "conflict",
    "confidence_band",
    "hybrid_score",
    "top_probability",
    "screen_strength",
    "screen_red_flag",
    "yes_count",
    "unknown_count",
]


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> Path:
    """Create the assessment_logs table if it does not exist."""

    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS assessment_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anon_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                screen_class TEXT,
                model_label TEXT,
                risk_level TEXT,
                conflict TEXT,
                confidence_band TEXT,
                hybrid_score REAL,
                top_probability REAL,
                screen_strength REAL,
                screen_red_flag INTEGER,
                yes_count INTEGER,
                unknown_count INTEGER,
                screening_answers_json TEXT NOT NULL,
                screening_triage_json TEXT,
                form_payload_json TEXT NOT NULL,
                model_result_json TEXT,
                decision_json TEXT NOT NULL,
                profile_json TEXT
            )
            """
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_assessment_logs_created_at "
            "ON assessment_logs(created_at DESC)"
        )
        connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_assessment_logs_anon_id "
            "ON assessment_logs(anon_id)"
        )
        connection.commit()
    return DB_PATH


def _json_dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def insert_assessment(payload: dict[str, Any]) -> dict[str, Any]:
    """Insert one anonymous assessment run. Returns the stored summary row."""

    init_db()
    anon_id = str(payload.get("anon_id") or "").strip()[:64]
    if not anon_id:
        raise ValueError("anon_id_required")

    screening_answers = payload.get("screening_answers")
    if not isinstance(screening_answers, dict):
        raise ValueError("screening_answers_required")

    form_payload = payload.get("form_payload")
    if not isinstance(form_payload, dict):
        raise ValueError("form_payload_required")

    decision = payload.get("decision")
    if not isinstance(decision, dict):
        raise ValueError("decision_required")

    created_at = datetime.now(timezone.utc).isoformat()
    screen_class = str(
        payload.get("screen_class")
        or decision.get("screen_class")
        or ""
    )[:64] or None
    model_label = str(payload.get("model_label") or "")[:64] or None
    risk_level = str(
        payload.get("risk_level") or decision.get("risk_level") or ""
    )[:32] or None
    conflict = decision.get("conflict")
    conflict_text = str(conflict)[:64] if conflict else None
    confidence_band = str(decision.get("confidence_band") or "")[:16] or None
    hybrid_score = _as_float(decision.get("hybrid_score"))
    top_probability = _as_float(decision.get("top_probability"))
    screen_strength = _as_float(decision.get("screen_strength"))
    screen_red_flag = 1 if decision.get("screen_red_flag") else 0
    yes_count = _as_int(payload.get("yes_count"))
    unknown_count = _as_int(payload.get("unknown_count"))

    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO assessment_logs (
                anon_id, created_at, screen_class, model_label, risk_level, conflict,
                confidence_band, hybrid_score, top_probability, screen_strength,
                screen_red_flag, yes_count, unknown_count,
                screening_answers_json, screening_triage_json, form_payload_json,
                model_result_json, decision_json, profile_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                anon_id,
                created_at,
                screen_class,
                model_label,
                risk_level,
                conflict_text,
                confidence_band,
                hybrid_score,
                top_probability,
                screen_strength,
                screen_red_flag,
                yes_count,
                unknown_count,
                _json_dump(screening_answers),
                _json_dump(payload.get("screening_triage")),
                _json_dump(form_payload),
                _json_dump(payload.get("model_result")),
                _json_dump(decision),
                _json_dump(payload.get("profile")),
            ),
        )
        row_id = int(cursor.lastrowid)
        connection.commit()

    return {
        "id": row_id,
        "anon_id": anon_id,
        "created_at": created_at,
        "screen_class": screen_class,
        "model_label": model_label,
        "risk_level": risk_level,
        "conflict": conflict_text,
        "confidence_band": confidence_band,
        "hybrid_score": hybrid_score,
        "top_probability": top_probability,
        "screen_strength": screen_strength,
        "screen_red_flag": bool(screen_red_flag),
        "yes_count": yes_count,
        "unknown_count": unknown_count,
    }


def _row_summary(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "anon_id": row["anon_id"],
        "created_at": row["created_at"],
        "screen_class": row["screen_class"],
        "model_label": row["model_label"],
        "risk_level": row["risk_level"],
        "conflict": row["conflict"],
        "confidence_band": row["confidence_band"],
        "hybrid_score": row["hybrid_score"],
        "top_probability": row["top_probability"],
        "screen_strength": row["screen_strength"],
        "screen_red_flag": bool(row["screen_red_flag"]),
        "yes_count": row["yes_count"],
        "unknown_count": row["unknown_count"],
    }


def _row_detail(row: sqlite3.Row) -> dict[str, Any]:
    detail = _row_summary(row)
    detail.update(
        {
            "screening_answers": json.loads(row["screening_answers_json"] or "{}"),
            "screening_triage": json.loads(row["screening_triage_json"] or "null"),
            "form_payload": json.loads(row["form_payload_json"] or "{}"),
            "model_result": json.loads(row["model_result_json"] or "null"),
            "decision": json.loads(row["decision_json"] or "{}"),
            "profile": json.loads(row["profile_json"] or "null"),
        }
    )
    return detail


def list_people(limit: int = 200) -> dict[str, Any]:
    """List anonymous people (anon_id) with run counts for per-person loading."""

    init_db()
    limit = max(1, min(int(limit), 500))
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT anon_id,
                   COUNT(*) AS runs,
                   MAX(id) AS last_id,
                   MAX(created_at) AS last_at
            FROM assessment_logs
            GROUP BY anon_id
            ORDER BY last_id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        total_people = connection.execute(
            "SELECT COUNT(DISTINCT anon_id) AS n FROM assessment_logs"
        ).fetchone()["n"]
    return {
        "total_people": int(total_people),
        "people": [
            {
                "anon_id": row["anon_id"],
                "runs": int(row["runs"]),
                "last_id": int(row["last_id"]),
                "last_at": row["last_at"],
            }
            for row in rows
        ],
    }


def list_assessments(
    limit: int = 100,
    offset: int = 0,
    detail: bool = False,
    anon_id: str | None = None,
    enrich: bool = False,
) -> dict[str, Any]:
    """Return newest assessment logs first, optionally filtered by anon_id."""

    init_db()
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))
    anon = str(anon_id).strip() if anon_id else None
    with _connect() as connection:
        if anon:
            total = connection.execute(
                "SELECT COUNT(*) AS n FROM assessment_logs WHERE anon_id = ?",
                (anon,),
            ).fetchone()["n"]
            rows = connection.execute(
                """
                SELECT * FROM assessment_logs
                WHERE anon_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (anon, limit, offset),
            ).fetchall()
        else:
            total = connection.execute("SELECT COUNT(*) AS n FROM assessment_logs").fetchone()["n"]
            rows = connection.execute(
                """
                SELECT * FROM assessment_logs
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
    # Detail or enrich both need JSON payloads.
    mapped = [_row_detail(row) if (detail or enrich) else _row_summary(row) for row in rows]
    if enrich:
        from log_compare import enrich_assessment_rows

        mapped = enrich_assessment_rows(mapped)
        if not detail:
            # Keep list payloads lighter.
            for item in mapped:
                item.pop("screening_answers", None)
                item.pop("screening_triage", None)
                item.pop("form_payload", None)
                item.pop("model_result", None)
                item.pop("decision", None)
                item.pop("profile", None)
                item.pop("gt_rule_triage", None)
    return {
        "total": int(total),
        "limit": limit,
        "offset": offset,
        "anon_id": anon,
        "rows": mapped,
    }


def get_assessment(row_id: int, enrich: bool = True) -> dict[str, Any] | None:
    init_db()
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM assessment_logs WHERE id = ?",
            (int(row_id),),
        ).fetchone()
    if row is None:
        return None
    detail = _row_detail(row)
    if enrich:
        from log_compare import enrich_assessment_row

        detail["_keep_triage_detail"] = True
        detail = enrich_assessment_row(detail)
        detail.pop("_keep_triage_detail", None)
    return detail


def _payload_age(form_payload: Any, profile: Any) -> float | None:
    for source in (form_payload, profile):
        if not isinstance(source, dict):
            continue
        raw = source.get("Age", source.get("age"))
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if math.isfinite(value):
            return value
    return None


def _payload_bmi_category(form_payload: Any, profile: Any) -> str | None:
    for source in (profile, form_payload):
        if not isinstance(source, dict):
            continue
        value = source.get("BMI Category") or source.get("bmi_category")
        if value:
            return str(value)
    return None


def prior_from_similar_logs(
    *,
    screen_class: str,
    model_label: str,
    age: float | None,
    bmi_category: str | None,
    min_similar: int = 3,
    age_window: float = 10.0,
    exclude_id: int | None = None,
) -> dict[str, Any]:
    """Build a decision prior from anonymous logs that look like the current case.

    Similarity: same screen_class + model_label, age within ±window, same BMI category.
    Escalation (never lowers risk): among similar rows, conflict_rate >= 0.40 or
    high_risk_rate >= 0.50, and similar_count >= min_similar.
    """

    init_db()
    screen_class = str(screen_class or "None")
    model_label = str(model_label or "")
    bmi_category = str(bmi_category or "").strip() or None

    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT * FROM assessment_logs
            WHERE screen_class = ? AND model_label = ?
            ORDER BY id DESC
            """,
            (screen_class, model_label),
        ).fetchall()

    similar: list[dict[str, Any]] = []
    for row in rows:
        if exclude_id is not None and int(row["id"]) == int(exclude_id):
            continue
        detail = _row_detail(row)
        row_age = _payload_age(detail.get("form_payload"), detail.get("profile"))
        row_bmi = _payload_bmi_category(detail.get("form_payload"), detail.get("profile"))
        if age is not None:
            if row_age is None or abs(row_age - float(age)) > float(age_window):
                continue
        if bmi_category is not None:
            if row_bmi is None or row_bmi != bmi_category:
                continue
        similar.append(detail)

    total = len(similar)
    conflict_count = sum(1 for item in similar if item.get("conflict"))
    high_count = sum(1 for item in similar if str(item.get("risk_level") or "") == "High")
    medium_count = sum(1 for item in similar if str(item.get("risk_level") or "") == "Medium")
    low_count = sum(1 for item in similar if str(item.get("risk_level") or "") == "Low")
    conflict_rate = (conflict_count / total) if total else None
    high_risk_rate = (high_count / total) if total else None
    eligible = total >= int(min_similar)
    escalate = False
    reasons: list[str] = []
    if eligible:
        if conflict_rate is not None and conflict_rate >= 0.40:
            escalate = True
            reasons.append("conflict_rate")
        if high_risk_rate is not None and high_risk_rate >= 0.50:
            escalate = True
            reasons.append("high_risk_rate")

    return {
        "kind": "log_prior",
        "match": {
            "screen_class": screen_class,
            "model_label": model_label,
            "age": age,
            "age_window": age_window,
            "bmi_category": bmi_category,
        },
        "min_similar": int(min_similar),
        "similar_count": total,
        "eligible": eligible,
        "conflict_count": conflict_count,
        "high_count": high_count,
        "medium_count": medium_count,
        "low_count": low_count,
        "conflict_rate": conflict_rate,
        "high_risk_rate": high_risk_rate,
        "escalate": escalate,
        "reasons": reasons,
        "note": (
            "Anonymous log prior for decision support. Requires enough similar "
            "cases before it can escalate caution. It never lowers risk."
        ),
    }


def export_assessments_csv() -> str:
    """CSV with questionnaire flats, GT columns, comparisons, and JSON blobs."""

    init_db()
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM assessment_logs ORDER BY id ASC"
        ).fetchall()
    from log_compare import enrich_assessment_rows

    enriched = enrich_assessment_rows([_row_detail(row) for row in rows])
    output = io.StringIO()
    q_cols = [f"q{i}" for i in range(1, 14)]
    q_num_cols = [f"q{i}_num" for i in range(1, 14)]
    # Prefer numeric compare columns for Sheets averages / charts.
    gt_cols = [
        "screen_class_code",
        "model_label_code",
        "risk_code",
        "gt_rule_class",
        "gt_rule_class_code",
        "gt_rule_see_doctor",
        "gt_rule_see_doctor_num",
        "gt_proxy_class",
        "gt_proxy_class_code",
        "gt_proxy_see_doctor",
        "gt_proxy_see_doctor_num",
        "gt_proxy_similar_count",
        "gt_proxy_confidence",
        "gt_proxy_eligible",
        "system_see_doctor",
        "system_see_doctor_num",
        "match_rule_vs_screen",
        "match_rule_vs_screen_num",
        "match_rule_vs_model",
        "match_rule_vs_model_num",
        "match_proxy_vs_model",
        "match_proxy_vs_model_num",
        "match_rule_vs_proxy",
        "match_rule_vs_proxy_num",
        "match_see_doctor_rule",
        "match_see_doctor_rule_num",
        "match_see_doctor_proxy",
        "match_see_doctor_proxy_num",
        "questionnaire_yes_score",
        "questionnaire_yes_rate",
        "agreement_score",
        "hybrid_model_weight",
        "hybrid_screen_weight",
        "score_why",
        "score_why_th",
        "class_code_legend",
        "match_code_legend",
    ]
    fieldnames = EXPORT_COLUMNS + q_cols + q_num_cols + gt_cols + [
        "screening_answers_json",
        "screening_triage_json",
        "form_payload_json",
        "model_result_json",
        "decision_json",
        "profile_json",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for item in enriched:
        flat = {
            **{key: item.get(key) for key in EXPORT_COLUMNS},
            **{key: item.get(key) for key in q_cols},
            **{key: item.get(key) for key in q_num_cols},
            **{key: item.get(key) for key in gt_cols},
            "screening_answers_json": json.dumps(item.get("screening_answers") or {}, ensure_ascii=False),
            "screening_triage_json": json.dumps(item.get("screening_triage"), ensure_ascii=False),
            "form_payload_json": json.dumps(item.get("form_payload") or {}, ensure_ascii=False),
            "model_result_json": json.dumps(item.get("model_result"), ensure_ascii=False),
            "decision_json": json.dumps(item.get("decision") or {}, ensure_ascii=False),
            "profile_json": json.dumps(item.get("profile"), ensure_ascii=False),
        }
        writer.writerow(flat)
    return output.getvalue()
