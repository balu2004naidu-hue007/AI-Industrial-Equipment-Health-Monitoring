from pathlib import Path
import sys

import pytest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from data_logger import parse_serial_line


def test_parse_line_with_mode():
    row = parse_serial_line("72.5,4.8,1480,7.0,224,1568,2.35,29,75,681.2,WARNING")
    assert row["machine_mode"] == "WARNING"
    assert row["temperature"] == 72.5


def test_parse_line_without_mode_uses_default():
    row = parse_serial_line("72.5,4.8,1480,7.0,224,1568,2.35,29,75,681.2", "NORMAL")
    assert row["machine_mode"] == "NORMAL"


def test_reject_wrong_field_count():
    with pytest.raises(ValueError, match="Expected 10 numeric values"):
        parse_serial_line("72.5,4.8,1480")


def test_ignore_blank_and_comment():
    assert parse_serial_line("") is None
    assert parse_serial_line("# device booting") is None
