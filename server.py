"""Local web server for the sleep-health decision support demo.

The browser is plain HTML, CSS, and JavaScript. This process only scores
records and prepares chart data by calling model.py.
"""

from __future__ import annotations

import math
from contextlib import asynccontextmanager
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import Body, FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from model import (
    CLASS_ORDER,
    GENDERS,
    INPUT_LIMITS,
    OCCUPATIONS,
    OTHER_OCCUPATION,
    TARGET,
    InputError,
    get_bundle,
    predict_record,
)

ROOT = Path(__file__).resolve().parent
WEB_DIR = ROOT / "web"
ASSET_DIR = ROOT / "assets"
WEIGHT_LIMITS_KG = (30.0, 250.0)
HEIGHT_LIMITS_CM = (120.0, 220.0)
HEATMAP_COLUMNS = [
    "Stress Level",
    "Sleep Duration",
    "Quality of Sleep",
    "Systolic_BP",
    "Diastolic_BP",
    "Disorder Risk",
]

BUNDLE: dict | None = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Train or load the cached pipeline once, before requests arrive."""

    global BUNDLE
    BUNDLE = get_bundle()
    yield


app = FastAPI(title="Sleep Health", lifespan=lifespan)
app.mount("/assets", StaticFiles(directory=ASSET_DIR), name="assets")
app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


def bmi_category_of(bmi: float) -> str:
    """Map one BMI value onto the adult category the model expects."""

    if bmi < 18.5:
        return "Underweight"
    if bmi < 25.0:
        return "Normal"
    if bmi < 30.0:
        return "Overweight"
    return "Obese"


def format_bmi(bmi: float, category: str) -> str:
    """Show one decimal, or two when rounding would imply another category."""

    if bmi_category_of(round(bmi, 1)) != category:
        return f"{bmi:.2f}"
    return f"{bmi:.1f}"


def sanitize(value: object) -> object:
    """Turn numpy values into JSON values."""

    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): sanitize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [sanitize(item) for item in value]
    if isinstance(value, (np.floating, float)):
        number = float(value)
        if not math.isfinite(number):
            return None
        return number
    if isinstance(value, (np.integer, int)):
        return int(value)
    return value


def _number(payload: dict, key: str) -> float | None:
    try:
        number = float(payload[key])
    except (KeyError, TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _metrics_payload(meta: dict) -> dict:
    metrics = meta["metrics"]

    def pack(stats: dict) -> dict:
        return {"mean": float(stats["mean"]), "std": float(stats["std"])}

    source = str(meta.get("source_path", ""))
    return {
        "folds": int(metrics["folds"]),
        "row_count": int(meta["row_count"]),
        "accuracy": pack(metrics["accuracy"]),
        "precision_macro": pack(metrics["precision_macro"]),
        "recall_macro": pack(metrics["recall_macro"]),
        "f1_macro": pack(metrics["f1_macro"]),
        "per_class": {
            label: {
                key: pack(metrics["per_class"][label][key])
                for key in ("precision", "recall", "f1")
            }
            for label in CLASS_ORDER
        },
        "class_counts": {label: int(meta["class_counts"].get(label, 0)) for label in CLASS_ORDER},
        "duplicate_feature_rows": int(meta["duplicate_feature_rows"]),
        "bmi_relabeled": int(meta["bmi_relabeled"]),
        "caveat": bool(meta.get("caveat")),
        "source_kind": "synthetic" if source == "synthetic" else "file",
        "source_name": Path(source).name if source else "",
    }


def _bundle() -> dict:
    if BUNDLE is None:
        raise RuntimeError("The model is not loaded.")
    return BUNDLE


@app.get("/")
def index() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/api/meta")
def meta() -> dict:
    """Return form choices and the age bounds of the training table."""

    frame = _bundle()["frame"]
    return {
        "genders": list(GENDERS),
        "occupations": list(OCCUPATIONS) + [OTHER_OCCUPATION],
        "limits": {feature: [float(low), float(high)] for feature, (low, high) in INPUT_LIMITS.items()},
        "weight_limits": list(WEIGHT_LIMITS_KG),
        "height_limits": list(HEIGHT_LIMITS_CM),
        "filter_genders": sorted(frame["Gender"].astype(str).unique()),
        "filter_occupations": sorted(frame["Occupation"].astype(str).unique()),
        "age_min": int(frame["Age"].min()),
        "age_max": int(frame["Age"].max()),
    }


@app.post("/api/assess", response_model=None)
def assess(payload: dict = Body(...)) -> JSONResponse | dict:
    """Score one person from weight, height, and the model inputs."""

    errors: list[dict] = []
    weight = _number(payload, "weight_kg")
    height = _number(payload, "height_cm")
    if weight is None or not WEIGHT_LIMITS_KG[0] <= weight <= WEIGHT_LIMITS_KG[1]:
        errors.append({"code": "weight_range"})
    if height is None or not HEIGHT_LIMITS_CM[0] <= height <= HEIGHT_LIMITS_CM[1]:
        errors.append({"code": "height_range"})
    if errors:
        return JSONResponse(status_code=400, content={"errors": errors})

    bmi = weight / ((height / 100.0) ** 2)
    category = bmi_category_of(bmi)
    model_payload = {
        "Gender": payload.get("Gender"),
        "Age": payload.get("Age"),
        "Occupation": payload.get("Occupation"),
        "BMI Category": category,
        "Sleep Duration": payload.get("Sleep Duration"),
        "Quality of Sleep": payload.get("Quality of Sleep"),
        "Physical Activity Level": payload.get("Physical Activity Level"),
        "Stress Level": payload.get("Stress Level"),
        "Daily Steps": payload.get("Daily Steps"),
        "Systolic_BP": payload.get("Systolic_BP"),
        "Diastolic_BP": payload.get("Diastolic_BP"),
        "Heart Rate": payload.get("Heart Rate"),
    }
    try:
        result = predict_record(_bundle(), model_payload)
    except InputError as exc:
        items = []
        for message in exc.errors:
            if "higher than diastolic" in message:
                items.append({"code": "bp_order"})
            else:
                items.append({"code": "model", "message": message})
        return JSONResponse(status_code=400, content={"errors": items})

    body = {
        "weight_kg": weight,
        "height_cm": height,
        "bmi": bmi,
        "bmi_display": format_bmi(bmi, category),
        "category": category,
    }
    return sanitize({
        "label": result["label"],
        "risk_level": result["recommendation"]["risk_level"],
        "probabilities": result["probabilities"],
        "factors": result["factors"],
        "importances": result["importances"],
        "support_notes": result["support_notes"],
        "profile": {key: model_payload[key] for key in model_payload if key != "BMI Category"} | {
            "BMI Category": category
        },
        "body": body,
    })


@app.post("/api/eda")
def eda(payload: dict = Body(...)) -> dict:
    """Filter the training table for charts. Cross-validation stays on the full table."""

    bundle = _bundle()
    frame = bundle["frame"]
    meta = bundle["meta"]
    response = {
        "training_rows": int(len(frame)),
        "age_min": int(frame["Age"].min()),
        "age_max": int(frame["Age"].max()),
        "metrics": _metrics_payload(meta),
        "status": "ok",
        "filtered_rows": 0,
        "class_counts": {},
    }
    genders = [str(value) for value in payload.get("genders") or []]
    occupations = [str(value) for value in payload.get("occupations") or []]
    if not genders or not occupations:
        response["status"] = "need_filter"
        return response

    try:
        age_min = int(payload.get("age_min"))
        age_max = int(payload.get("age_max"))
    except (TypeError, ValueError):
        age_min = response["age_min"]
        age_max = response["age_max"]
    if age_min > age_max:
        age_min, age_max = age_max, age_min

    filtered = frame[
        frame["Gender"].isin(genders)
        & frame["Occupation"].isin(occupations)
        & frame["Age"].between(age_min, age_max)
    ].copy()
    if filtered.empty:
        response["status"] = "empty"
        return response

    response["filtered_rows"] = int(len(filtered))
    response["class_counts"] = {
        label: int((filtered[TARGET] == label).sum()) for label in CLASS_ORDER
    }
    response["heatmap"] = _heatmap(filtered)
    response["scatter"] = _scatter(filtered)
    response["prevalence"] = _prevalence(filtered)
    return response


def _heatmap(filtered: pd.DataFrame) -> dict | None:
    if len(filtered) < 3:
        return None
    corr = filtered.loc[:, HEATMAP_COLUMNS].corr(numeric_only=True)
    matrix = []
    for row_name in HEATMAP_COLUMNS:
        matrix.append([
            None if pd.isna(corr.loc[row_name, column]) else round(float(corr.loc[row_name, column]), 4)
            for column in HEATMAP_COLUMNS
        ])
    pearson = corr.loc["Stress Level", "Sleep Duration"]
    return {
        "columns": list(HEATMAP_COLUMNS),
        "matrix": matrix,
        "pearson": None if pd.isna(pearson) else round(float(pearson), 4),
    }


def _scatter(filtered: pd.DataFrame) -> dict:
    points = [
        {
            "sleep": float(row["Sleep Duration"]),
            "stress": float(row["Stress Level"]),
            "label": str(row[TARGET]),
            "gender": str(row["Gender"]),
            "occupation": str(row["Occupation"]),
            "bmi": str(row["BMI Category"]),
            "quality": float(row["Quality of Sleep"]),
            "age": float(row["Age"]),
        }
        for _, row in filtered.iterrows()
    ]
    medians: dict[str, dict] = {}
    for label in CLASS_ORDER:
        part = filtered[filtered[TARGET] == label]
        if part.empty:
            continue
        medians[label] = {
            "hours": float(part["Sleep Duration"].median()),
            "stress": float(part["Stress Level"].median()),
        }
    overlap = int(filtered.duplicated(subset=["Sleep Duration", "Stress Level"]).sum())
    return {"points": points, "medians": medians, "overlap": overlap}


def _prevalence(filtered: pd.DataFrame) -> dict:
    groups = []
    for occupation in sorted(filtered["Occupation"].astype(str).unique()):
        part = filtered[filtered["Occupation"] == occupation]
        total = int(len(part))
        for label in CLASS_ORDER:
            count = int((part[TARGET] == label).sum())
            groups.append({
                "occupation": occupation,
                "label": label,
                "count": count,
                "percent": (100.0 * count / total) if total else 0.0,
                "total": total,
            })
    apnea = [row for row in groups if row["label"] == "Sleep Apnea"]
    if not apnea:
        note = {"kind": "empty"}
    elif max(row["percent"] for row in apnea) == 0:
        note = {"kind": "zero"}
    else:
        stable = [row for row in apnea if row["total"] >= 10]
        pool = stable or apnea
        top = sorted(pool, key=lambda row: (row["percent"], row["count"]), reverse=True)[0]
        note = {
            "kind": "stable" if stable else "any",
            "job": top["occupation"],
            "percent": int(round(top["percent"])),
            "count": int(top["count"]),
            "total": int(top["total"]),
        }
    return {"groups": groups, "note": note}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8765)
