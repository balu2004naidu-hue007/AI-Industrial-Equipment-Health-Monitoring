#!/usr/bin/env python3
"""Stream clearly simulated machine readings into the live CSV for laptop demos."""
from __future__ import annotations

import argparse
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from industrial_monitoring.core import append_machine_reading

SCENARIOS = ("NORMAL", "WARNING", "BEARING_FAULT", "OVERLOAD", "COOLING_FAULT")


def generate_reading(mode: str, rng: random.Random) -> dict[str, float | str]:
    distributions = {
        "NORMAL": ((63, 4), (3.2, .5), (1500, 25), (6.3, .5), (225, 4), (2.3, .15), (28, 2), (65, 7)),
        "WARNING": ((72, 5), (4.8, .7), (1480, 35), (7.0, .6), (224, 5), (2.35, .18), (29, 2), (75, 7)),
        "BEARING_FAULT": ((82, 6), (8.5, 1.2), (1440, 50), (7.6, .8), (224, 5), (2.3, .2), (29, 2), (78, 8)),
        "OVERLOAD": ((86, 6), (6.5, 1.0), (1370, 60), (9.2, .9), (222, 5), (2.5, .2), (30, 2), (92, 4)),
        "COOLING_FAULT": ((92, 6), (3.7, .6), (1490, 30), (6.7, .5), (225, 4), (2.2, .2), (30, 2), (67, 7)),
    }
    if mode not in distributions:
        raise ValueError(f"Unsupported scenario: {mode}")
    samples = [rng.gauss(mean, sigma) for mean, sigma in distributions[mode]]
    temperature, vibration, rpm, current, voltage, pressure, ambient, load = samples
    current = max(0.1, current)
    voltage = max(1.0, voltage)
    return {
        "temperature": round(temperature, 2),
        "vibration": round(max(0, vibration), 2),
        "rpm": round(max(0, rpm), 1),
        "motor_current": round(current, 2),
        "voltage": round(voltage, 2),
        "power": round(voltage * current, 2),
        "pressure": round(max(0, pressure), 2),
        "ambient_temperature": round(ambient, 2),
        "load": round(max(0, load), 2),
        "running_hours": round(680 + rng.random() * 0.01, 3),
        "machine_mode": mode,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", choices=["cycle", "normal", "warning", "bearing_fault", "overload", "cooling_fault"], default="cycle")
    parser.add_argument("--count", type=int, default=0, help="Number of readings; 0 runs until Ctrl+C")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between readings")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "live_machine_data.csv")
    args = parser.parse_args()
    if args.count < 0 or args.interval < 0:
        parser.error("--count and --interval must be non-negative")
    rng = random.Random(args.seed)
    fixed_mode = args.scenario.upper()
    if fixed_mode == "CYCLE":
        print("Demo scenarios cycle through normal, warning, bearing, overload and cooling patterns.")
    else:
        print(f"Generating simulated {fixed_mode} readings.")
    print(f"Output: {args.output} | Ctrl+C to stop")
    index = 0
    try:
        while args.count == 0 or index < args.count:
            mode = SCENARIOS[(index // 10) % len(SCENARIOS)] if fixed_mode == "CYCLE" else fixed_mode
            row = append_machine_reading(args.output, generate_reading(mode, rng))
            index += 1
            print(f"{index:05d} | {row['timestamp']} | {mode:<13} | T={row['temperature']:>6.2f} °C | VIB={row['vibration']:>5.2f} mm/s | RPM={row['rpm']:>6.1f}")
            if args.count == 0 or index < args.count:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
