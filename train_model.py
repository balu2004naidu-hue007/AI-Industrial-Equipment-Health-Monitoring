#!/usr/bin/env python3
"""Train and evaluate the synthetic-data binary predictive-maintenance model."""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from industrial_monitoring.training import train_predictive_model


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=ROOT / "data" / "training_data.csv")
    parser.add_argument("--models-dir", type=Path, default=ROOT / "models")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    result = train_predictive_model(args.data, args.models_dir, args.seed)
    metrics = result["metrics"]
    print("Predictive maintenance baseline trained.")
    print(f"Rows: {metrics['total_rows']} | Accuracy: {metrics['accuracy']:.1%} | Balanced accuracy: {metrics['balanced_accuracy']:.1%} | Macro F1: {metrics['macro_f1']:.3f}")
    print("Confusion matrix (true rows, predicted columns; labels 0,1):")
    for row in metrics["confusion_matrix_labels_0_1"]:
        print(row)
    print(f"Saved model and metadata to: {args.models_dir}")
    print("CAUTION: metrics are from synthetic generated data; they are not real-world accuracy claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
