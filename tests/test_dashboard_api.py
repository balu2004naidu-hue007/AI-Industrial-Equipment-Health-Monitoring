import json
from http.server import ThreadingHTTPServer
from pathlib import Path
import sys
from threading import Thread
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from dashboard import DashboardApp, create_handler
from simulate_machine import generate_reading
from industrial_monitoring.core import append_machine_reading
import random


def test_dashboard_live_api_returns_assessment(tmp_path):
    csv_path = tmp_path / "live.csv"
    append_machine_reading(csv_path, generate_reading("BEARING_FAULT", random.Random(7)), timestamp="2026-11-08T12:00:00+00:00")
    app = DashboardApp(csv_path, tmp_path / "no-models", stale_after=3600)
    server = ThreadingHTTPServer(("127.0.0.1", 0), create_handler(app))
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/api/live", timeout=3) as response:
            payload = json.load(response)
        assert payload["ok"] is True
        assert payload["latest"]["machine_mode"] == "BEARING_FAULT"
        assert payload["analysis"]["status"] == "CRITICAL"
        assert payload["analysis"]["diagnosis"] == "Bearing / mechanical fault pattern"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_dashboard_reports_empty_data(tmp_path):
    app = DashboardApp(tmp_path / "missing.csv", tmp_path / "no-models", stale_after=10)
    payload = app.snapshot()
    assert payload["ok"] is False
    assert payload["latest"] is None
    assert any("No valid machine readings" in warning for warning in payload["warnings"])
