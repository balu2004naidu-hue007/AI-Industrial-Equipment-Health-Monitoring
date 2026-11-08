#!/usr/bin/env python3
"""Generate a reproducible synthetic machine-condition training dataset."""
from __future__ import annotations

import argparse
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent


def generate_dataset(samples_per_mode: int = 1000, seed: int = 42) -> pd.DataFrame:
    if samples_per_mode < 20:
        raise ValueError("samples_per_mode must be at least 20")
    rng = np.random.default_rng(seed)
    specifications = {
        "NORMAL": ((63, 4), (3.2, 0.5), (1500, 25), (6.3, 0.5), (225, 4), (2.3, 0.15), (28, 2), (65, 7), 0),
        "WARNING": ((72, 5), (4.8, 0.7), (1480, 35), (7.0, 0.6), (224, 5), (2.35, 0.18), (29, 2), (75, 7), 1),
        "BEARING_FAULT": ((82, 6), (8.5, 1.2), (1440, 50), (7.6, 0.8), (224, 5), (2.3, 0.2), (29, 2), (78, 8), 1),
        "OVERLOAD": ((86, 6), (6.5, 1.0), (1370, 60), (9.2, 0.9), (222, 5), (2.5, 0.2), (30, 2), (92, 4), 1),
        "COOLING_FAULT": ((92, 6), (3.7, 0.6), (1490, 30), (6.7, 0.5), (225, 4), (2.2, 0.2), (30, 2), (67, 7), 1),
    }
    rows = []
    for mode, spec in specifications.items():
        distributions, failure = spec[:-1], spec[-1]
        columns = [rng.normal(mean, std, samples_per_mode) for mean, std in distributions]
        temp, vibration, rpm, current, voltage, pressure, ambient, load = columns
        for idx in range(samples_per_mode):
            rows.append({
                "temperature": float(np.clip(temp[idx], 40, 120)),
                "vibration": float(np.clip(vibration[idx], 0.5, 15)),
                "rpm": float(np.clip(rpm[idx], 1000, 1700)),
                "motor_current": float(np.clip(current[idx], 3, 15)),
                "voltage": float(np.clip(voltage[idx], 200, 245)),
                "pressure": float(np.clip(pressure[idx], 1, 4)),
                "ambient_temperature": float(np.clip(ambient[idx], 15, 45)),
                "load": float(np.clip(load[idx], 20, 100)),
                "power": float(max(0, voltage[idx] * current[idx])),
                "running_hours": float(rng.uniform(100, 5000)),
                "machine_mode": mode,
                "failure": failure,
            })
    frame = pd.DataFrame(rows)
    return frame.sample(frac=1, random_state=seed).reset_index(drop=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples-per-mode", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "training_data.csv")
    args = parser.parse_args()
    frame = generate_dataset(args.samples_per_mode, args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.output, index=False, float_format="%.6f")
    print(f"Saved {len(frame):,} synthetic rows to {args.output}")
    print("Machine-mode counts:")
    print(frame["machine_mode"].value_counts().sort_index().to_string())
    print("Failure labels:")
    print(frame["failure"].value_counts().sort_index().to_string())
    print("NOTE: This is generated demonstration data, not measured industrial telemetry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
