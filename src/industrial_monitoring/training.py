"""Reproducible model training routines for the simulated training dataset."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .core import ANOMALY_FEATURES, MODEL_FEATURES


def load_training_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Training dataset not found: {path}. Run python generate_training_data.py first.")
    frame = pd.read_csv(path)
    required = set(MODEL_FEATURES) | {"failure", "machine_mode"}
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Training dataset is missing required columns: {', '.join(missing)}")
    frame = frame.dropna(subset=list(required)).copy()
    if len(frame) < 100:
        raise ValueError(f"At least 100 valid training rows are required; found {len(frame)}")
    frame["failure"] = pd.to_numeric(frame["failure"], errors="raise").astype(int)
    labels = set(frame["failure"].unique())
    if not labels.issubset({0, 1}) or len(labels) != 2:
        raise ValueError("The failure target must contain both binary labels 0 and 1")
    for column in MODEL_FEATURES:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=list(MODEL_FEATURES))
    if frame[list(MODEL_FEATURES)].isna().any().any():
        raise ValueError("Training features still contain missing values after cleaning")
    return frame


def train_predictive_model(data_path: Path, models_dir: Path, random_state: int = 42) -> dict[str, Any]:
    import joblib

    frame = load_training_data(data_path)
    x = frame[list(MODEL_FEATURES)]
    y = frame["failure"]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=0.20, random_state=random_state, stratify=y
    )
    model = RandomForestClassifier(
        n_estimators=300, max_depth=15, min_samples_split=4,
        min_samples_leaf=2, class_weight="balanced", random_state=random_state, n_jobs=-1,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    report = classification_report(y_test, predictions, output_dict=True, zero_division=0)
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1]).tolist()
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_test, predictions)), 4),
        "macro_f1": round(float(f1_score(y_test, predictions, average="macro")), 4),
        "confusion_matrix_labels_0_1": matrix,
        "classification_report": report,
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "total_rows": int(len(frame)),
        "class_counts": {str(int(k)): int(v) for k, v in y.value_counts().sort_index().items()},
    }
    feature_importance = sorted(
        ({"feature": name, "importance": round(float(score), 6)} for name, score in zip(MODEL_FEATURES, model.feature_importances_)),
        key=lambda item: item["importance"], reverse=True,
    )
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, models_dir / "predictive_maintenance_model.joblib")
    metadata = {
        "model": "RandomForestClassifier",
        "features": list(MODEL_FEATURES),
        "target": "failure (0=normal, 1=abnormal/fault pattern)",
        "training_data": str(data_path.as_posix()),
        "training_data_is_synthetic": True,
        "random_state": random_state,
        "metrics": metrics,
        "feature_importance": feature_importance,
        "limitations": [
            "Metrics are measured on a random holdout from generated synthetic data.",
            "The data is not a field dataset and does not establish real-equipment accuracy.",
            "The model is an educational baseline, not a safety or shutdown controller.",
        ],
    }
    (models_dir / "predictive_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def train_anomaly_model(data_path: Path, models_dir: Path, random_state: int = 42) -> dict[str, Any]:
    import joblib

    frame = load_training_data(data_path)
    normal = frame.loc[frame["failure"].astype(int) == 0, list(ANOMALY_FEATURES)]
    if len(normal) < 50:
        raise ValueError(f"At least 50 normal rows are required to train anomaly detection; found {len(normal)}")
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("isolation_forest", IsolationForest(n_estimators=300, contamination=0.03, random_state=random_state, n_jobs=-1)),
    ])
    model.fit(normal)
    models_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, models_dir / "anomaly_detection_model.joblib")
    metadata = {
        "model": "StandardScaler + IsolationForest",
        "features": list(ANOMALY_FEATURES),
        "training_rows": int(len(normal)),
        "training_subset": "rows labelled failure=0 only",
        "training_data_is_synthetic": True,
        "contamination_setting": 0.03,
        "random_state": random_state,
        "limitations": [
            "Isolation Forest detects deviation from this synthetic normal baseline.",
            "Anomaly is not proof of a machine fault; validate thresholds on real plant data.",
        ],
    }
    (models_dir / "anomaly_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata
