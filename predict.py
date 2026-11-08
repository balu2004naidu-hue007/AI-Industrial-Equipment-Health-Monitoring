#!/usr/bin/env python3
"""Analyse the latest valid reading and append a consistent prediction record."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from industrial_monitoring.core import analyze_reading, load_models, read_machine_rows

RESULT_FIELDS = ["timestamp", "machine_mode", "risk_score", "health_score", "status", "anomaly_status", "diagnosis", "model_failure_probability", "rul_proxy_hours", "recommendation"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "live_machine_data.csv")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "models")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "prediction_results.csv")
    args = parser.parse_args()
    try:
        rows, warnings = read_machine_rows(args.data, limit=1)
    except Exception as exc:
        print(f"ERROR reading input data: {exc}", file=sys.stderr)
        return 1
    if not rows:
        print("No valid machine reading is available. Run the simulator or serial logger first.", file=sys.stderr)
        return 1
    latest = rows[-1]
    models = load_models(args.models_dir)
    result = analyze_reading(latest, models)
    record = {**latest, **result}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_header = not args.output.exists() or args.output.stat().st_size == 0
    with args.output.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS, extrasaction="ignore")
        if write_header:
            writer.writeheader()
        writer.writerow(record)
    print(json.dumps(record, indent=2, allow_nan=False))
    if warnings or models.warnings:
        for warning in [*warnings, *models.warnings]:
            print(f"WARNING: {warning}", file=sys.stderr)
    print(f"Saved consistent prediction record to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
