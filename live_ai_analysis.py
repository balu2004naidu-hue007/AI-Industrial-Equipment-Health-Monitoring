#!/usr/bin/env python3
"""Backward-compatible one-shot analysis that writes data/ai_results.json."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from industrial_monitoring.core import analyze_reading, load_models, read_machine_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "live_machine_data.csv")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "models")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "ai_results.json")
    args = parser.parse_args()
    try:
        rows, warnings = read_machine_rows(args.data, limit=1)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if not rows:
        print("No valid reading found. Start the simulator or serial logger.", file=sys.stderr)
        return 1
    row = rows[-1]
    models = load_models(args.models_dir)
    result = {**row, **analyze_reading(row, models)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps(result, indent=2, allow_nan=False))
    for warning in [*warnings, *models.warnings]:
        print(f"WARNING: {warning}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
