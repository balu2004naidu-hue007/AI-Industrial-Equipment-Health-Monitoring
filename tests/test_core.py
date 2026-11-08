from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from industrial_monitoring.core import (
    CSV_FIELDS, ModelBundle, analyze_reading, append_machine_reading,
    read_machine_rows, sensor_risk, validate_machine_values,
)
from simulate_machine import generate_reading
import random


def test_simulator_reading_matches_csv_schema():
    reading = generate_reading("NORMAL", random.Random(1))
    validated = validate_machine_values(reading)
    assert tuple(["timestamp"] + list(validated)) == CSV_FIELDS
    assert validated["machine_mode"] == "NORMAL"


def test_risk_detects_fault_pattern():
    rng = random.Random(5)
    normal = validate_machine_values(generate_reading("NORMAL", rng))
    fault = validate_machine_values(generate_reading("BEARING_FAULT", rng))
    assert sensor_risk(fault) > sensor_risk(normal)
    assert analyze_reading(fault, ModelBundle())["status"] == "CRITICAL"


def test_invalid_sensor_value_is_rejected():
    row = generate_reading("NORMAL", random.Random(2))
    row["temperature"] = float("nan")
    with pytest.raises(ValueError, match="finite"):
        validate_machine_values(row)


def test_invalid_mode_is_rejected():
    row = generate_reading("NORMAL", random.Random(2))
    row["machine_mode"] = "MAINTENANCE_NOW"
    with pytest.raises(ValueError, match="Unknown machine_mode"):
        validate_machine_values(row)


def test_append_and_read_csv(tmp_path):
    output = tmp_path / "machine.csv"
    reading = generate_reading("NORMAL", random.Random(7))
    append_machine_reading(output, reading, timestamp="2026-11-08T12:00:00+00:00")
    rows, warnings = read_machine_rows(output)
    assert not warnings
    assert len(rows) == 1
    assert rows[0]["machine_mode"] == "NORMAL"


def test_existing_wrong_schema_is_not_overwritten(tmp_path):
    output = tmp_path / "machine.csv"
    original = "Time,Temperature\nnoon,70\n"
    output.write_text(original)
    with pytest.raises(ValueError, match="schema mismatch"):
        append_machine_reading(output, generate_reading("NORMAL", random.Random(9)))
    assert output.read_text() == original
