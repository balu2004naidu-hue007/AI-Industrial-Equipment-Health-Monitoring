#!/usr/bin/env python3
"""Train an Isolation Forest baseline using only synthetic normal rows."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from industrial_monitoring.training import train_anomaly_model


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "training_data.csv")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "models")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = train_anomaly_model(args.data, args.models_dir, args.seed)
    print(f"Anomaly detector trained using {result['training_rows']} synthetic normal rows.")
    print(f"Saved model and metadata to: {args.models_dir}")
    print("CAUTION: anomaly means deviation from the generated baseline, not proof of failure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
