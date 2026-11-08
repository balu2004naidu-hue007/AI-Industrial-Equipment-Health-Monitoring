"""Shared data validation, model loading, and condition analysis.

The bundled training data is simulated. Model scores are useful for software
experiments only and must not be treated as calibrated safety probabilities.
"""
from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

NUMERIC_FIELDS = (
    "temperature", "vibration", "rpm", "motor_current", "voltage", "power",
    "pressure", "ambient_temperature", "load", "running_hours",
)
SERIAL_FIELDS = NUMERIC_FIELDS + ("machine_mode",)
CSV_FIELDS = ("timestamp",) + SERIAL_FIELDS
MODEL_FEATURES = NUMERIC_FIELDS
ANOMALY_FEATURES = (
    "temperature", "vibration", "rpm", "motor_current", "voltage",
    "pressure", "ambient_temperature", "load", "power",
)
MACHINE_MODES = {"NORMAL", "WARNING", "BEARING_FAULT", "OVERLOAD", "COOLING_FAULT"}
FAULT_MODES = {"BEARING_FAULT", "OVERLOAD", "COOLING_FAULT"}
MODE_LABELS = {
    "NORMAL": "Normal operation",
    "WARNING": "Abnormal operating condition",
    "BEARING_FAULT": "Bearing fault pattern",
    "OVERLOAD": "Motor overload pattern",
    "COOLING_FAULT": "Cooling fault pattern",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_timestamp(value: Any) -> datetime | None:
    if value is None or not str(value).strip():
        return None
    try:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def finite_float(value: Any, field: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be numeric; received {value!r}") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} must be a finite number")
    return result


def validate_machine_values(values: dict[str, Any], default_mode: str = "NORMAL") -> dict[str, Any]:
    """Validate one reading and normalize it to the CSV schema (without timestamp)."""
    missing = [name for name in NUMERIC_FIELDS if name not in values]
    if missing:
        raise ValueError(f"Missing numeric fields: {', '.join(missing)}")

    row: dict[str, Any] = {name: finite_float(values[name], name) for name in NUMERIC_FIELDS}
    limits = {
        "temperature": (-20, 200), "vibration": (0, 100), "rpm": (0, 20000),
        "motor_current": (0, 1000), "voltage": (0, 1000), "power": (0, 1_000_000),
        "pressure": (0, 1000), "ambient_temperature": (-50, 100),
        "load": (0, 150), "running_hours": (0, 1_000_000_000),
    }
    for field, (low, high) in limits.items():
        if not low <= row[field] <= high:
            raise ValueError(f"{field}={row[field]} is outside the accepted input range [{low}, {high}]")

    if row["power"] == 0 and row["voltage"] > 0 and row["motor_current"] > 0:
        row["power"] = row["voltage"] * row["motor_current"]

    mode = str(values.get("machine_mode", default_mode)).strip().upper() or default_mode
    if mode not in MACHINE_MODES:
        raise ValueError(f"Unknown machine_mode {mode!r}; expected one of {', '.join(sorted(MACHINE_MODES))}")
    row["machine_mode"] = mode
    return row


def validate_csv_header(path: Path) -> None:
    if not path.exists() or path.stat().st_size == 0:
        return
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        actual = next(csv.reader(handle), [])
    if actual != list(CSV_FIELDS):
        raise ValueError(
            f"CSV schema mismatch in {path}. Expected header: {','.join(CSV_FIELDS)}. "
            "Back up or rename the existing file before starting a new log."
        )


def append_machine_reading(path: Path, values: dict[str, Any], timestamp: str | None = None) -> dict[str, Any]:
    """Append one validated reading. A wrong existing schema is never overwritten."""
    path.parent.mkdir(parents=True, exist_ok=True)
    validate_csv_header(path)
    reading = validate_machine_values(values)
    write_header = not path.exists() or path.stat().st_size == 0
    row = {"timestamp": timestamp or utc_now_iso(), **reading}
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(row)
        handle.flush()
    return row


def read_machine_rows(path: Path, limit: int = 180) -> tuple[list[dict[str, Any]], list[str]]:
    """Read valid rows; return rows and non-fatal validation warnings."""
    if not path.exists():
        return [], [f"Live data file not found: {path}"]
    if path.stat().st_size == 0:
        return [], ["Live data file is empty."]
    validate_csv_header(path)
    rows: list[dict[str, Any]] = []
    warnings: list[str] = []
    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for line_number, raw in enumerate(reader, start=2):
            if not raw or not any((v or "").strip() for v in raw.values()):
                continue
            try:
                timestamp = str(raw.get("timestamp", "")).strip()
                if parse_timestamp(timestamp) is None:
                    raise ValueError("timestamp is missing or invalid")
                reading = validate_machine_values(raw)
                rows.append({"timestamp": timestamp, **reading})
            except ValueError as exc:
                warnings.append(f"Skipped CSV row {line_number}: {exc}")
    return rows[-limit:], warnings


@dataclass
class ModelBundle:
    predictive_model: Any = None
    anomaly_model: Any = None
    predictive_metadata: dict[str, Any] | None = None
    anomaly_metadata: dict[str, Any] | None = None
    warnings: tuple[str, ...] = ()


def load_models(models_dir: Path) -> ModelBundle:
    """Load locally generated joblib models, if present.

    Only load model files that you trained yourself from this repository's
    scripts. As with pickle, joblib files can execute code while loading.
    """
    warnings: list[str] = []
    bundle = ModelBundle()
    try:
        import joblib
    except ImportError:
        return ModelBundle(warnings=("joblib is not installed; run pip install -r requirements.txt",))

    predictive_path = models_dir / "predictive_maintenance_model.joblib"
    anomaly_path = models_dir / "anomaly_detection_model.joblib"
    predictive_meta = models_dir / "predictive_metadata.json"
    anomaly_meta = models_dir / "anomaly_metadata.json"

    if predictive_path.exists():
        try:
            bundle.predictive_model = joblib.load(predictive_path)
            if predictive_meta.exists():
                bundle.predictive_metadata = json.loads(predictive_meta.read_text(encoding="utf-8"))
        except Exception as exc:  # report, do not crash the monitoring dashboard
            warnings.append(f"Predictive model could not be loaded: {exc}")
    else:
        warnings.append("Predictive model not trained yet. Run: python train_model.py")

    if anomaly_path.exists():
        try:
            bundle.anomaly_model = joblib.load(anomaly_path)
            if anomaly_meta.exists():
                bundle.anomaly_metadata = json.loads(anomaly_meta.read_text(encoding="utf-8"))
        except Exception as exc:
            warnings.append(f"Anomaly model could not be loaded: {exc}")
    else:
        warnings.append("Anomaly model not trained yet. Run: python train_anomaly_model.py")

    bundle.warnings = tuple(warnings)
    return bundle


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def sensor_risk(row: dict[str, Any]) -> float:
    """Transparent rule-based screening score; not a calibrated probability."""
    risks = [
        _clamp((row["temperature"] - 55.0) / 35.0 * 100),
        _clamp((row["vibration"] - 1.5) / 7.0 * 100),
        _clamp((row["load"] - 55.0) / 45.0 * 100),
        _clamp((row["motor_current"] - 4.0) / 7.0 * 100),
        _clamp(max(0.0, abs(row["pressure"] - 2.3) - 1.0) / 3.0 * 100),
        _clamp(abs(row["voltage"] - 230.0) / 18.0 * 100),
        _clamp(abs(row["rpm"] - 1500.0) / 450.0 * 100),
    ]
    weighted = sum(score * weight for score, weight in zip(risks, (0.24, 0.22, 0.18, 0.14, 0.07, 0.08, 0.07)))
    mode_boost = {"NORMAL": 0, "WARNING": 12, "BEARING_FAULT": 24, "OVERLOAD": 25, "COOLING_FAULT": 24}.get(row["machine_mode"], 0)
    return _clamp(weighted + mode_boost)


def _model_failure_probability(model: Any, row: dict[str, Any]) -> float | None:
    if model is None or not hasattr(model, "predict_proba"):
        return None
    try:
        sample = pd.DataFrame([{name: row[name] for name in MODEL_FEATURES}], columns=MODEL_FEATURES)
        probabilities = model.predict_proba(sample)[0]
        classes = list(model.classes_)
        positive_index = classes.index(1) if 1 in classes else None
        if positive_index is None:
            return None
        return _clamp(float(probabilities[positive_index]) * 100)
    except Exception:
        return None


def _anomaly_status(model: Any, row: dict[str, Any]) -> str:
    if model is None:
        return "NOT TRAINED"
    try:
        sample = pd.DataFrame([{name: row[name] for name in ANOMALY_FEATURES}], columns=ANOMALY_FEATURES)
        return "ANOMALY" if int(model.predict(sample)[0]) == -1 else "NORMAL"
    except Exception:
        return "UNAVAILABLE"


def analyze_reading(row: dict[str, Any], models: ModelBundle | None = None) -> dict[str, Any]:
    models = models or ModelBundle()
    srisk = sensor_risk(row)
    model_probability = _model_failure_probability(models.predictive_model, row)
    risk_score = srisk if model_probability is None else _clamp(0.65 * srisk + 0.35 * model_probability)
    anomaly_status = _anomaly_status(models.anomaly_model, row)

    mode = row["machine_mode"]
    if mode == "BEARING_FAULT":
        diagnosis = "Bearing / mechanical fault pattern"
        recommendation = "Inspect bearing condition, lubrication, alignment and vibration source. Follow site lockout/tagout procedures before intervention."
    elif mode == "OVERLOAD":
        diagnosis = "Motor overload pattern"
        recommendation = "Review machine load and motor current. Check for mechanical resistance and confirm drive protection settings."
    elif mode == "COOLING_FAULT":
        diagnosis = "Cooling system fault pattern"
        recommendation = "Inspect airflow, fan operation and heat dissipation. Reduce operation only under the site's approved procedure if temperature remains high."
    elif row["vibration"] >= 7:
        diagnosis = "Elevated vibration pattern"
        recommendation = "Inspect vibration source, mounting, alignment and bearing condition. Compare with the machine's rated vibration limits."
    elif row["temperature"] >= 85:
        diagnosis = "Elevated temperature pattern"
        recommendation = "Check cooling, lubrication, ambient conditions and the machine's rated temperature limit."
    elif row["motor_current"] >= 9 or row["load"] >= 90:
        diagnosis = "High current / load pattern"
        recommendation = "Review load and current trend; inspect drive and mechanical resistance against equipment ratings."
    elif mode == "WARNING" or risk_score >= 40 or anomaly_status == "ANOMALY":
        diagnosis = "Abnormal operating pattern"
        recommendation = "Continue close monitoring and schedule an inspection using the site's maintenance procedure."
    else:
        diagnosis = "No critical pattern detected"
        recommendation = "Continue routine monitoring and scheduled preventive maintenance."

    status = "CRITICAL" if mode in FAULT_MODES or risk_score >= 70 else "WARNING" if risk_score >= 40 else "HEALTHY"
    health_score = round(100.0 - risk_score, 1)
    rul_proxy = round(max(40.0, 900.0 * (1.0 - risk_score / 100.0)), 1)

    return {
        "risk_score": round(risk_score, 1),
        "health_score": health_score,
        "status": status,
        "anomaly_status": anomaly_status,
        "diagnosis": diagnosis,
        "rul_proxy_hours": rul_proxy,
        "recommendation": recommendation,
        "sensor_risk_score": round(srisk, 1),
        "model_failure_probability": None if model_probability is None else round(model_probability, 1),
        "model_source": "synthetic-training-data model" if model_probability is not None else "rule-based sensor score only",
        "rul_note": "Illustrative heuristic only; not a trained or validated remaining-useful-life estimate.",
    }
