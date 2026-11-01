"""Sleep-disorder risk model: prepare data, train, evaluate, and explain.

The classifier predicts one of three labels: None, Insomnia, or Sleep Apnea.
Cross-validation uses stratified folds and reports accuracy plus macro
precision, recall, and F1. A fitted pipeline is cached as a joblib artifact.
"""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
DATA_FILENAME = "Sleep_health_and_lifestyle_dataset.csv"
DATA_CANDIDATES = [
    ROOT / DATA_FILENAME,
    Path.home() / "Downloads" / DATA_FILENAME,
]
ARTIFACT_DIR = ROOT / "artifacts"
PIPELINE_PATH = ARTIFACT_DIR / "sleep_disorder_pipeline.joblib"
METRICS_PATH = ARTIFACT_DIR / "cv_metrics.json"
MODEL_VERSION = "1"

TARGET = "Sleep Disorder"
CLASS_ORDER = ["None", "Insomnia", "Sleep Apnea"]
RISK_RANK = {"None": 0, "Insomnia": 1, "Sleep Apnea": 2}

CATEGORICAL = ["Gender", "Occupation", "BMI Category"]
NUMERIC = [
    "Age",
    "Sleep Duration",
    "Quality of Sleep",
    "Physical Activity Level",
    "Stress Level",
    "Heart Rate",
    "Daily Steps",
    "Systolic_BP",
    "Diastolic_BP",
]
FEATURES = CATEGORICAL + NUMERIC
RAW_NUMERIC = [
    "Age",
    "Sleep Duration",
    "Quality of Sleep",
    "Physical Activity Level",
    "Stress Level",
    "Heart Rate",
    "Daily Steps",
]

GENDERS = ["Female", "Male"]
OCCUPATIONS = [
    "Accountant",
    "Doctor",
    "Engineer",
    "Lawyer",
    "Manager",
    "Nurse",
    "Sales Representative",
    "Salesperson",
    "Scientist",
    "Software Engineer",
    "Teacher",
]
BMI_CATEGORIES = ["Underweight", "Normal", "Overweight", "Obese"]

# Widget bounds for the assessment form. Wider than the training sample so a
# person can enter a plausible value that the dataset itself does not contain.
INPUT_LIMITS = {
    "Age": (18, 65),
    "Sleep Duration": (3.0, 12.0),
    "Quality of Sleep": (1, 10),
    "Physical Activity Level": (0, 180),
    "Stress Level": (1, 10),
    "Daily Steps": (0, 20000),
    "Systolic_BP": (80, 200),
    "Diastolic_BP": (40, 130),
    "Heart Rate": (40, 140),
}

DISPLAY_NAMES = {
    "Age": "Age",
    "Sleep Duration": "Sleep duration",
    "Quality of Sleep": "Sleep quality",
    "Physical Activity Level": "Physical activity",
    "Stress Level": "Stress level",
    "Heart Rate": "Heart rate",
    "Daily Steps": "Daily steps",
    "Systolic_BP": "Systolic blood pressure",
    "Diastolic_BP": "Diastolic blood pressure",
    "Gender": "Gender",
    "Occupation": "Occupation",
    "BMI Category": "BMI category",
}

RECOMMENDATIONS = {
    "None": {
        "risk_level": "Low",
        "decision": "Maintain current routine.",
        "actions": [
            "Keep a regular sleep and wake schedule.",
            "Sleep in a dark, quiet room.",
            "Limit caffeine in the hours before bed.",
        ],
    },
    "Insomnia": {
        "risk_level": "Medium",
        "decision": "Behavioral and lifestyle intervention.",
        "actions": [
            "Practice stress management and relaxation techniques.",
            "Limit screen time for one hour before sleep.",
            "Consider consulting a wellness coach.",
        ],
    },
    "Sleep Apnea": {
        "risk_level": "High",
        "decision": "Medical evaluation required.",
        "actions": [
            "Treat this result as a red flag, not a diagnosis.",
            "Schedule a clinical polysomnography (sleep test).",
            "Consult a pulmonologist or sleep specialist.",
        ],
    },
}

CV_FOLDS = 5
RANDOM_STATE = 42


class InputError(ValueError):
    """Raised when an assessment form payload cannot be scored."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


def load_raw_dataframe() -> pd.DataFrame:
    """Load the project CSV, then the Downloads copy, then a synthetic set.

    The literal label ``None`` must survive import. pandas would otherwise
    treat that word as a missing value and drop the majority class.
    """

    for path in DATA_CANDIDATES:
        if path.is_file():
            frame = pd.read_csv(path, keep_default_na=False, encoding="utf-8-sig")
            frame.columns = [str(column).strip() for column in frame.columns]
            frame.attrs["source_path"] = str(path)
            return frame

    frame = _synthesize_dataset()
    frame.attrs["source_path"] = "synthetic"
    return frame


def prepare_frame(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Engineer blood pressure and BMI, then keep rows that can be modeled."""

    frame = raw.copy()
    bmi = frame["BMI Category"].astype(str).str.strip()
    info = {
        "source_path": raw.attrs.get("source_path", "unknown"),
        "bmi_relabeled": int((bmi == "Normal Weight").sum()),
        "rows_in_file": int(len(frame)),
    }
    frame["BMI Category"] = bmi.replace({"Normal Weight": "Normal"})
    frame["Gender"] = frame["Gender"].astype(str).str.strip()
    frame["Occupation"] = frame["Occupation"].astype(str).str.strip()

    for column in RAW_NUMERIC:
        frame[column] = pd.to_numeric(frame[column].replace({"": pd.NA}), errors="coerce")

    blood_pressure = (
        frame["Blood Pressure"]
        .astype(str)
        .str.strip()
        .str.replace(" ", "", regex=False)
        .str.split("/", n=1, expand=True)
    )
    frame["Systolic_BP"] = pd.to_numeric(blood_pressure[0], errors="coerce")
    frame["Diastolic_BP"] = pd.to_numeric(blood_pressure[1], errors="coerce")

    target = frame[TARGET].astype(str).str.strip()
    missing_target = target.eq("") | target.str.lower().isin(["nan", "none", "<na>"])
    frame[TARGET] = target.mask(missing_target, "None")

    prepared = frame.dropna(subset=FEATURES + [TARGET]).copy()
    prepared = prepared[prepared[TARGET].isin(CLASS_ORDER)].reset_index(drop=True)
    prepared["Disorder Risk"] = prepared[TARGET].map(RISK_RANK).astype(int)
    info["rows_used"] = int(len(prepared))
    info["rows_dropped"] = int(len(frame) - len(prepared))
    return prepared, info


def build_pipeline() -> Pipeline:
    """One-hot encode categories, scale numbers, then fit a random forest."""

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
            ("numeric", StandardScaler(), NUMERIC),
        ]
    )
    classifier = RandomForestClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=1,
    )
    return Pipeline([
        ("preprocess", preprocessor),
        ("model", classifier),
    ])


def cross_validate_model(pipeline: Pipeline, features: pd.DataFrame, target: pd.Series) -> dict:
    """Evaluate accuracy and macro precision, recall, and F1 on stratified folds."""

    smallest_class = int(target.value_counts().min())
    if smallest_class < CV_FOLDS:
        raise ValueError(
            f"Need at least {CV_FOLDS} rows in every class for stratified CV; "
            f"the smallest class has {smallest_class}."
        )

    splitter = StratifiedKFold(
        n_splits=CV_FOLDS,
        shuffle=True,
        random_state=RANDOM_STATE,
    )
    fold_accuracy: list[float] = []
    fold_precision: list[float] = []
    fold_recall: list[float] = []
    fold_f1: list[float] = []
    per_class = {
        label: {"precision": [], "recall": [], "f1": []}
        for label in CLASS_ORDER
    }

    for train_index, test_index in splitter.split(features, target):
        candidate = clone(pipeline)
        candidate.fit(features.iloc[train_index], target.iloc[train_index])
        predicted = candidate.predict(features.iloc[test_index])
        actual = target.iloc[test_index]
        fold_accuracy.append(float(accuracy_score(actual, predicted)))

        macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
            actual,
            predicted,
            labels=CLASS_ORDER,
            average="macro",
            zero_division=0,
        )
        fold_precision.append(float(macro_precision))
        fold_recall.append(float(macro_recall))
        fold_f1.append(float(macro_f1))

        class_precision, class_recall, class_f1, _ = precision_recall_fscore_support(
            actual,
            predicted,
            labels=CLASS_ORDER,
            average=None,
            zero_division=0,
        )
        for index, label in enumerate(CLASS_ORDER):
            per_class[label]["precision"].append(float(class_precision[index]))
            per_class[label]["recall"].append(float(class_recall[index]))
            per_class[label]["f1"].append(float(class_f1[index]))

    metrics = {
        "accuracy": _mean_std(fold_accuracy),
        "precision_macro": _mean_std(fold_precision),
        "recall_macro": _mean_std(fold_recall),
        "f1_macro": _mean_std(fold_f1),
        "per_class": {
            label: {metric: _mean_std(values) for metric, values in scores.items()}
            for label, scores in per_class.items()
        },
        "folds": CV_FOLDS,
    }
    return metrics


def get_bundle(force_retrain: bool = False) -> dict:
    """Return the trained pipeline, evaluation metadata, and analysis table."""

    raw = load_raw_dataframe()
    frame, prep_info = prepare_frame(raw)
    signature = _signature(frame, prep_info)
    if not force_retrain and _cache_matches(signature):
        pipeline = joblib.load(PIPELINE_PATH)
        meta = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    else:
        pipeline, meta = _train_and_cache(frame, prep_info, signature)
    return {"pipeline": pipeline, "frame": frame, "meta": meta}


def predict_record(bundle: dict, payload: dict) -> dict:
    """Score one person and attach profile-based reasons plus the decision."""

    record = coerce_record(payload)
    row = pd.DataFrame([{column: record[column] for column in FEATURES}])
    pipeline = bundle["pipeline"]
    probabilities_array = pipeline.predict_proba(row)[0]
    classes = list(pipeline.named_steps["model"].classes_)
    by_class = {
        label: float(probability)
        for label, probability in zip(classes, probabilities_array)
    }
    label = classes[int(np.argmax(probabilities_array))]
    return {
        "label": label,
        "probabilities": {name: by_class.get(name, 0.0) for name in CLASS_ORDER},
        "factors": explain_record(bundle, record, label),
        "importances": bundle["meta"]["importances"],
        "recommendation": RECOMMENDATIONS[label],
        "support_notes": _support_notes(bundle, record),
    }


def coerce_record(payload: dict) -> dict:
    """Validate one assessment and return model-ready feature values."""

    errors: list[str] = []
    record: dict = {}

    gender = str(payload.get("Gender", "")).strip()
    if gender not in GENDERS:
        errors.append("Gender must be Female or Male.")
    else:
        record["Gender"] = gender

    occupation = str(payload.get("Occupation", "")).strip()
    if occupation not in OCCUPATIONS:
        errors.append("Occupation is not one of the supported roles.")
    else:
        record["Occupation"] = occupation

    bmi = str(payload.get("BMI Category", "")).strip()
    if bmi == "Normal Weight":
        bmi = "Normal"
    if bmi not in BMI_CATEGORIES:
        errors.append("BMI category must be Underweight, Normal, Overweight, or Obese.")
    else:
        record["BMI Category"] = bmi

    integer_fields = {
        "Age",
        "Quality of Sleep",
        "Physical Activity Level",
        "Stress Level",
        "Daily Steps",
        "Systolic_BP",
        "Diastolic_BP",
        "Heart Rate",
    }
    for feature, (low, high) in INPUT_LIMITS.items():
        value = _as_float(feature, payload.get(feature), low, high, errors)
        if value is None:
            continue
        record[feature] = int(round(value)) if feature in integer_fields else float(value)

    systolic = record.get("Systolic_BP")
    diastolic = record.get("Diastolic_BP")
    if systolic is not None and diastolic is not None and systolic <= diastolic:
        errors.append("Systolic blood pressure must be higher than diastolic blood pressure.")

    if errors:
        raise InputError(errors)
    return record


def explain_record(bundle: dict, record: dict, label: str) -> list[dict]:
    """Compare the person with class medians on the most important features.

    These notes describe association in the training table. They are not
    causal effects and they are not a medical diagnosis.
    """

    meta = bundle["meta"]
    profiles = meta["profiles"]
    if "None" not in profiles or label not in profiles:
        return []

    importance = {item["feature"]: item["importance"] for item in meta["importances"]}
    none_median = profiles["None"]["numeric_median"]
    predicted_median = profiles[label]["numeric_median"]
    ranked: list[tuple[float, dict]] = []

    for feature in NUMERIC:
        user_value = float(record[feature])
        none_value = float(none_median[feature])
        predicted_value = float(predicted_median[feature])
        shift = predicted_value - none_value
        if label == "None":
            scale = meta["numeric_std"].get(feature) or 1.0
            score = importance.get(feature, 0.0) / (1.0 + abs(user_value - none_value) / scale)
        elif abs(shift) < 1e-9:
            continue
        else:
            covered = (user_value - none_value) / shift
            score = importance.get(feature, 0.0) * max(min(covered, 1.5), 0.0)
        ranked.append((
            score,
            {
                "feature": feature,
                "kind": "numeric",
                "importance": importance.get(feature, 0.0),
                "sentence": _numeric_sentence(
                    feature, user_value, none_value, predicted_value, label
                ),
            },
        ))

    ranked.sort(key=lambda item: item[0], reverse=True)
    if label != "None":
        aligned = [factor for score, factor in ranked if score > 0]
        chosen = aligned[:3] if aligned else [factor for _, factor in ranked[:3]]
    else:
        chosen = [factor for _, factor in ranked[:3]]

    chosen.extend(_categorical_factors(meta, record, label))
    return chosen[:4]


def _train_and_cache(frame: pd.DataFrame, prep_info: dict, signature: str) -> tuple[Pipeline, dict]:
    features = frame.loc[:, FEATURES]
    target = frame[TARGET]
    pipeline = build_pipeline()
    metrics = cross_validate_model(pipeline, features, target)
    pipeline.fit(features, target)

    duplicate_rows = int(frame.duplicated(subset=FEATURES).sum())
    meta = {
        "model_version": MODEL_VERSION,
        "signature": signature,
        "source_path": prep_info["source_path"],
        "row_count": prep_info["rows_used"],
        "rows_dropped": prep_info["rows_dropped"],
        "bmi_relabeled": prep_info["bmi_relabeled"],
        "class_counts": {label: int(count) for label, count in target.value_counts().items()},
        "duplicate_feature_rows": duplicate_rows,
        "caveat": (
            "Some feature profiles are repeated. Stratified cross-validation can "
            "look optimistic because similar rows may appear in both the training "
            "and test folds."
            if duplicate_rows
            else ""
        ),
        "metrics": metrics,
        "importances": _grouped_importances(pipeline),
        "profiles": _class_profiles(frame),
        "numeric_std": {
            column: float(frame[column].std(ddof=0) or 0.0) for column in NUMERIC
        },
        "training_ranges": {
            column: {"min": float(frame[column].min()), "max": float(frame[column].max())}
            for column in NUMERIC
        },
        "known_categories": {
            column: sorted(frame[column].astype(str).unique())
            for column in CATEGORICAL
        },
        "categorical_rates": _categorical_rates(frame),
        "base_rates": {
            label: float(count) / float(len(frame))
            for label, count in target.value_counts().items()
        },
    }
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, PIPELINE_PATH)
    METRICS_PATH.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return pipeline, meta


def _class_profiles(frame: pd.DataFrame) -> dict:
    profiles = {}
    for label, part in frame.groupby(TARGET):
        profiles[str(label)] = {
            "count": int(len(part)),
            "numeric_median": {column: float(part[column].median()) for column in NUMERIC},
        }
    return profiles


def _categorical_rates(frame: pd.DataFrame) -> dict:
    rates: dict = {}
    for column in CATEGORICAL:
        rates[column] = {}
        for category, part in frame.groupby(column):
            counts = part[TARGET].value_counts()
            total = int(counts.sum())
            rates[column][str(category)] = {
                "count": total,
                "rates": {str(label): float(count) / total for label, count in counts.items()},
            }
    return rates


def _grouped_importances(pipeline: Pipeline) -> list[dict]:
    preprocessor = pipeline.named_steps["preprocess"]
    model = pipeline.named_steps["model"]
    grouped = {column: 0.0 for column in FEATURES}
    encoded_names = preprocessor.get_feature_names_out()
    for encoded_name, score in zip(encoded_names, model.feature_importances_):
        original = _original_feature(str(encoded_name))
        if original in grouped:
            grouped[original] += float(score)
    total = sum(grouped.values()) or 1.0
    rows = [
        {
            "feature": feature,
            "label": DISPLAY_NAMES[feature],
            "importance": grouped[feature] / total,
        }
        for feature in FEATURES
    ]
    rows.sort(key=lambda item: item["importance"], reverse=True)
    return rows


def _original_feature(encoded_name: str) -> str:
    rest = encoded_name.split("__", 1)[1] if "__" in encoded_name else encoded_name
    if rest in NUMERIC:
        return rest
    for column in CATEGORICAL:
        if rest == column or rest.startswith(column + "_"):
            return column
    return rest


def _categorical_factors(meta: dict, record: dict, label: str) -> list[dict]:
    factors = []
    base_rate = float(meta["base_rates"].get(label, 0.0))
    for feature in ("BMI Category", "Occupation"):
        category = str(record[feature])
        stats = meta["categorical_rates"].get(feature, {}).get(category)
        if not stats or stats["count"] < 10:
            continue
        rate = float(stats["rates"].get(label, 0.0))
        if rate < base_rate + 0.05:
            continue
        name = DISPLAY_NAMES[feature]
        factors.append({
            "feature": feature,
            "kind": "categorical",
            "importance": next(
                (item["importance"] for item in meta["importances"] if item["feature"] == feature),
                0.0,
            ),
            "sentence": (
                f"{name} is {category}. In this dataset, {rate:.0%} of {category} "
                f"records are labeled {label}, compared with {base_rate:.0%} overall."
            ),
        })
    factors.sort(key=lambda item: item["importance"], reverse=True)
    return factors[:1]


def _numeric_sentence(
    feature: str,
    user_value: float,
    none_value: float,
    predicted_value: float,
    label: str,
) -> str:
    name = DISPLAY_NAMES[feature]
    user_text = _pretty_number(feature, user_value)
    none_text = _pretty_number(feature, none_value)
    if label == "None":
        return (
            f"{name} is {user_text}, compared with the no-disorder median of {none_text}."
        )
    if user_value > none_value:
        relation = "higher than"
    elif user_value < none_value:
        relation = "lower than"
    else:
        relation = "equal to"
    predicted_text = _pretty_number(feature, predicted_value)
    return (
        f"{name} is {user_text}, {relation} the no-disorder median of {none_text}. "
        f"The {label} group median is {predicted_text}."
    )


def _pretty_number(feature: str, value: float) -> str:
    if feature in ("Quality of Sleep", "Stress Level"):
        return f"{value:.0f}/10"
    if feature == "Sleep Duration":
        return f"{value:.1f} hours"
    if feature == "Daily Steps":
        return f"{round(value):,.0f} steps"
    units = {
        "Physical Activity Level": "min/day",
        "Heart Rate": "bpm",
        "Systolic_BP": "mmHg",
        "Diastolic_BP": "mmHg",
        "Age": "years",
    }
    number = f"{value:.0f}" if abs(value - round(value)) < 1e-6 else f"{value:.1f}"
    unit = units.get(feature)
    return f"{number} {unit}" if unit else number


def _support_notes(bundle: dict, record: dict) -> list[str]:
    notes = []
    for feature, bounds in bundle["meta"]["training_ranges"].items():
        value = float(record[feature])
        if value < bounds["min"] or value > bounds["max"]:
            notes.append(
                f"{DISPLAY_NAMES[feature]} is outside the range observed in the "
                f"training data ({_pretty_number(feature, bounds['min'])} to "
                f"{_pretty_number(feature, bounds['max'])})."
            )
    for feature in CATEGORICAL:
        value = str(record[feature])
        if value not in bundle["meta"]["known_categories"].get(feature, []):
            notes.append(
                f"{DISPLAY_NAMES[feature]} value '{value}' does not appear in the training data."
            )
    return notes


def _signature(frame: pd.DataFrame, prep_info: dict) -> str:
    source = prep_info["source_path"]
    if source != "synthetic":
        stamp = Path(source).stat().st_mtime
    else:
        stamp = "synthetic"
    return f"{MODEL_VERSION}|{source}|{stamp}|{len(frame)}|{prep_info['bmi_relabeled']}"


def _cache_matches(signature: str) -> bool:
    if not PIPELINE_PATH.is_file() or not METRICS_PATH.is_file():
        return False
    try:
        cached = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return cached.get("signature") == signature and cached.get("model_version") == MODEL_VERSION


def _mean_std(values: list[float]) -> dict:
    array = np.asarray(values, dtype=float)
    return {
        "mean": float(array.mean()),
        "std": float(array.std(ddof=0)),
        "folds": [float(value) for value in array],
    }


def _as_float(feature: str, value: object, low: float, high: float, errors: list[str]) -> float | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        errors.append(f"{DISPLAY_NAMES[feature]} is required.")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append(f"{DISPLAY_NAMES[feature]} must be a number.")
        return None
    if not np.isfinite(number) or number < low or number > high:
        errors.append(f"{DISPLAY_NAMES[feature]} must be between {low:g} and {high:g}.")
        return None
    return number


def _synthesize_dataset(n: int = 400, seed: int = 42) -> pd.DataFrame:
    """Build a correlated stand-in only when no CSV can be found."""

    rng = np.random.default_rng(seed)
    occupations = np.array(OCCUPATIONS)
    bmi_levels = np.array(BMI_CATEGORIES)
    stress = rng.integers(3, 9, size=n)
    sleep = np.clip(9.1 - 0.34 * stress + rng.normal(0, 0.3, size=n), 4.5, 9.0)
    quality = np.clip(np.rint(10.5 - 0.7 * stress + rng.normal(0, 0.4, size=n)), 4, 9).astype(int)
    activity = rng.integers(30, 91, size=n)
    steps = np.clip(activity * 85 + rng.normal(0, 500, size=n), 3000, 12000).astype(int)
    bmi = rng.choice(bmi_levels, size=n, p=[0.05, 0.52, 0.33, 0.10])
    bmi_shift = {"Underweight": -8, "Normal": 0, "Overweight": 10, "Obese": 18}
    systolic = np.clip(
        np.rint(np.array([118 + bmi_shift[level] for level in bmi]) + rng.normal(0, 4, size=n)),
        100,
        170,
    ).astype(int)
    diastolic = np.clip(np.rint(systolic * 0.66 + rng.normal(0, 2, size=n)), 60, 110).astype(int)
    heart = np.clip(
        np.rint(62 + (systolic - 120) * 0.35 + rng.normal(0, 3, size=n)),
        55,
        100,
    ).astype(int)

    disorder: list[str] = []
    for index in range(n):
        apnea_score = int(bmi[index] in ("Overweight", "Obese")) + int(systolic[index] >= 135) + int(heart[index] >= 80)
        insomnia_score = int(stress[index] >= 7) + int(sleep[index] <= 6.2) + int(quality[index] <= 5)
        roll = float(rng.random())
        if apnea_score >= 2 and roll < 0.8:
            disorder.append("Sleep Apnea")
        elif insomnia_score >= 2 and roll < 0.85:
            disorder.append("Insomnia")
        elif roll < 0.05:
            disorder.append(str(rng.choice(["Insomnia", "Sleep Apnea"])))
        else:
            disorder.append("None")

    return pd.DataFrame({
        "Person ID": np.arange(1, n + 1),
        "Gender": rng.choice(["Male", "Female"], size=n),
        "Age": rng.integers(18, 66, size=n),
        "Occupation": rng.choice(occupations, size=n),
        "Sleep Duration": np.round(sleep, 1),
        "Quality of Sleep": quality,
        "Physical Activity Level": activity,
        "Stress Level": stress,
        "BMI Category": bmi,
        "Blood Pressure": [f"{sys}/{dia}" for sys, dia in zip(systolic, diastolic)],
        "Heart Rate": heart,
        "Daily Steps": steps,
        "Sleep Disorder": disorder,
    })


def main() -> None:
    bundle = get_bundle(force_retrain=True)
    meta = bundle["meta"]
    print(f"Source: {meta['source_path']}")
    print(f"Rows used: {meta['row_count']} (dropped {meta['rows_dropped']})")
    print(f"BMI 'Normal Weight' relabeled: {meta['bmi_relabeled']}")
    print(f"Class counts: {meta['class_counts']}")
    print(f"Duplicate feature rows: {meta['duplicate_feature_rows']}")
    for name in ("accuracy", "precision_macro", "recall_macro", "f1_macro"):
        stats = meta["metrics"][name]
        print(f"{name}: {stats['mean']:.3f} ± {stats['std']:.3f}")
    sample = bundle["frame"].iloc[0]
    prediction = predict_record(bundle, sample.loc[FEATURES].to_dict())
    print(f"Sample prediction: {prediction['label']} {prediction['probabilities']}")
    if meta["caveat"]:
        print(meta["caveat"])


if __name__ == "__main__":
    main()
