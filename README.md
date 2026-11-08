# AI Industrial Equipment Health Monitoring & Predictive Maintenance

**A laptop-runnable, AI-assisted industrial equipment monitoring prototype with a live browser dashboard, synthetic machine simulator, optional Arduino/serial ingestion, fault-pattern screening, and reproducible model training.**

> **Project scope:** This repository is an academic software prototype. The supplied 5,000-row training dataset and the laptop simulator are synthetic. No real plant dataset, verified sensor calibration, Arduino sketch, pin map, or physical machine test was included in the supplied project archive. The models and risk scores must not be presented as proven industrial failure predictions or used as a safety/protection system.

## What the project does

The system accepts ten machine parameters—temperature, vibration, RPM, motor current, voltage, power, pressure, ambient temperature, load, and running hours—plus an optional machine-mode label. It validates each reading, logs it to a common CSV file, analyses the latest reading, and displays the result in a local browser dashboard.

The project includes:

- **Live monitoring dashboard:** dark, responsive browser dashboard with status, risk index, health score, anomaly status, sensor tiles, trends, history, stale-data detection, and model availability notices.
- **Laptop demo mode:** a repeatable simulator that cycles through normal, warning, bearing-fault, overload, and cooling-fault patterns. It makes the full software workflow demonstrable without an Arduino or sensors.
- **Serial ingestion:** configurable COM/USB serial port, baud rate, validation, optional mode token, skipped-line reporting, and graceful shutdown.
- **Predictive baseline:** Random Forest classifier trained on the included synthetic binary labels, with holdout metrics and feature importance saved to JSON.
- **Anomaly baseline:** StandardScaler + Isolation Forest trained only on synthetic normal examples.
- **Condition assessment:** explicit sensor-risk scoring, ML estimate when the local model exists, diagnosis text, and maintenance guidance.
- **Automated checks:** pytest tests for schema validation, simulator, serial parser, scoring and model training, plus GitHub Actions CI.

## Quick start (Windows PowerShell)

Use Python 3.10–3.13. From the repository folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Generate the reproducible 5,000-row synthetic training set, then train both local models:

```powershell
python generate_training_data.py
python train_model.py
python train_anomaly_model.py
```

Start a 60-reading demonstration stream:

```powershell
python simulate_machine.py --scenario cycle --count 60 --interval 1
```

Start the dashboard in a second PowerShell window (activate the same environment first):

```powershell
python dashboard.py
```

Open **http://127.0.0.1:8501** in a browser. The dashboard refreshes every two seconds. For a continuous simulation, omit `--count`:

```powershell
python simulate_machine.py --scenario cycle --interval 1
```

Use `Ctrl+C` to stop the simulator or dashboard.

## Using a real serial device

The serial logger is optional; the simulator is the default laptop demonstration path. Connect only through correctly rated and isolated sensor interfaces. The supplied archive did not include the Arduino firmware, exact sensor models, pin mapping, or wiring diagram, so this repository deliberately does not invent those details.

For a Windows Arduino port such as COM7:

```powershell
python data_logger.py --port COM7 --baud 9600
```

To stop after 100 valid readings:

```powershell
python data_logger.py --port COM7 --baud 9600 --limit 100
```

The serial protocol and field order are specified in [`docs/serial_protocol.md`](docs/serial_protocol.md) and [`arduino_code/README.md`](arduino_code/README.md). By default, the last `machine_mode` field is optional and missing modes are logged as `NORMAL`. Confirm the sensor's units and scaling before connecting real hardware.

## Analyse the latest reading

Once `data/live_machine_data.csv` has one or more valid rows:

```powershell
python predict.py
```

This prints a single assessment and appends a row to `data/prediction_results.csv`. For the JSON-compatible one-shot output:

```powershell
python live_ai_analysis.py
```

The JSON result is written to `data/ai_results.json`.

## Project structure

```text
AI-Industrial-Equipment-Health-Monitoring/
├── README.md
├── requirements.txt
├── generate_training_data.py
├── train_model.py
├── train_anomaly_model.py
├── simulate_machine.py
├── data_logger.py
├── predict.py
├── live_ai_analysis.py
├── dashboard.py
├── src/industrial_monitoring/
│   ├── __init__.py
│   ├── core.py
│   └── training.py
├── data/
│   ├── README.md
│   └── sample_live_data.csv
├── models/README.md
├── arduino_code/README.md
├── docs/
│   ├── architecture.md
│   ├── model_and_data.md
│   └── serial_protocol.md
├── tests/
│   ├── test_core.py
│   ├── test_serial_parser.py
│   └── test_training.py
└── .github/workflows/tests.yml
```

Generated model binaries and live logs are intentionally excluded from Git. Create them locally with the model-training scripts and simulator/logger. A virtual environment such as `.venv/` must not be committed.

## Data and model interpretation

The generator creates 5,000 synthetic training records by default, evenly split across five generated operating modes. The generated training CSV is created locally with `python generate_training_data.py` and is not required to be committed. The binary target is 0 for the generated normal class and 1 for the four generated abnormal/fault-pattern classes. The Random Forest holdout metrics describe performance on a random subset of this generated dataset only; they do not demonstrate accuracy on a real motor or industrial plant.

The anomaly detector models deviation from the generated normal baseline. An anomaly is not proof of a fault. The dashboard's overall risk score is a screening index rather than a calibrated probability. The displayed RUL is explicitly an **illustrative heuristic proxy**, not a model trained on run-to-failure data. Read [`docs/model_and_data.md`](docs/model_and_data.md) before interpreting metrics.

## Tests

Install dependencies, then run:

```powershell
python -m pytest -q
```

The CI workflow runs these tests on Python 3.10, 3.11, and 3.12. The tests cover the software data path and model-building pipeline; they do not replace physical sensor, serial-device, or machine validation.

## Technology stack

Python · pandas · NumPy · scikit-learn · Joblib · pySerial · HTML/CSS/JavaScript · pytest · GitHub Actions

## Development status

**Software prototype: reproducible laptop demo and optional serial interface.** Physical hardware integration is not verified because the supplied project files did not include sensor wiring/firmware or real measured data. Future engineering work should replace the synthetic data, document actual sensors and their calibration, validate models on time-separated and machine-separated measured data, and test the full system under controlled conditions.

## Safety and limitations

This is not an industrial safety controller, protection relay, emergency-stop system, OEM diagnostic tool, or certified maintenance system. Do not connect high-voltage, mains, motor-drive, or industrial signals directly to a microcontroller. Use appropriate isolation and rated transducers. All operational decisions must follow the equipment manufacturer's documentation and the site's approved safety and maintenance procedures.

## Author

**Balaji Naidu V** · Electronics and Communication Engineering
