#!/usr/bin/env python3
"""Read the documented CSV serial protocol from an Arduino/USB serial device."""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from industrial_monitoring.core import NUMERIC_FIELDS, append_machine_reading, validate_machine_values


def parse_serial_line(line: str, default_mode: str = "NORMAL") -> dict[str, float | str] | None:
    """Parse 10 numeric CSV values plus an optional final machine-mode token."""
    text = line.strip()
    if not text or text.startswith("#"):
        return None
    values = next(csv.reader([text], skipinitialspace=True))
    values = [value.strip() for value in values]
    if values and values[0].lower() in {"temperature", "temp"}:
        return None  # optional header from a microcontroller
    if len(values) not in (len(NUMERIC_FIELDS), len(NUMERIC_FIELDS) + 1):
        raise ValueError(f"Expected {len(NUMERIC_FIELDS)} numeric values and an optional mode ({len(NUMERIC_FIELDS)} or {len(NUMERIC_FIELDS)+1} fields); received {len(values)}")
    raw = dict(zip(NUMERIC_FIELDS, values[:len(NUMERIC_FIELDS)]))
    raw["machine_mode"] = values[-1] if len(values) == len(NUMERIC_FIELDS) + 1 else default_mode
    return validate_machine_values(raw, default_mode=default_mode)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", default=os.getenv("INDUSTRIAL_SERIAL_PORT", "COM3"), help="Serial port, e.g. COM7 or /dev/ttyUSB0")
    parser.add_argument("--baud", type=int, default=9600)
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--default-mode", choices=["NORMAL", "WARNING", "BEARING_FAULT", "OVERLOAD", "COOLING_FAULT"], default="NORMAL")
    parser.add_argument("--output", type=Path, default=ROOT / "data" / "live_machine_data.csv")
    parser.add_argument("--limit", type=int, default=0, help="Stop after N valid readings; 0 runs until Ctrl+C")
    args = parser.parse_args()
    if args.baud <= 0 or args.timeout <= 0 or args.limit < 0:
        parser.error("baud and timeout must be positive; limit cannot be negative")
    try:
        import serial
    except ImportError:
        print("pyserial is missing. Install project dependencies with: python -m pip install -r requirements.txt", file=sys.stderr)
        return 2

    print(f"Opening {args.port} at {args.baud} baud. Output: {args.output}")
    device = None
    valid = skipped = 0
    try:
        device = serial.Serial(args.port, args.baud, timeout=args.timeout)
        time.sleep(2.0)  # allow common Arduino boards to reset after opening serial
        print("Serial connected. Waiting for readings; Ctrl+C stops safely.")
        while args.limit == 0 or valid < args.limit:
            raw = device.readline()
            if not raw:
                continue
            line = raw.decode("utf-8", errors="replace").strip()
            if not line:
                continue
            try:
                parsed = parse_serial_line(line, args.default_mode)
                if parsed is None:
                    continue
                row = append_machine_reading(args.output, parsed)
                valid += 1
                print(f"{valid:05d} | {row['machine_mode']:<13} | T={row['temperature']:.2f} °C | VIB={row['vibration']:.2f} mm/s | RPM={row['rpm']:.1f}")
            except ValueError as exc:
                skipped += 1
                print(f"Skipped serial row: {exc} | received={line!r}", file=sys.stderr)
    except KeyboardInterrupt:
        print("\nLogger stopped by user.")
    except (OSError, serial.SerialException) as exc:
        print(f"Could not read serial device {args.port}: {exc}", file=sys.stderr)
        return 1
    finally:
        if device is not None and device.is_open:
            device.close()
    print(f"Finished. Valid readings: {valid}; skipped lines: {skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
