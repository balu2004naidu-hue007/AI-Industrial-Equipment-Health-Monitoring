# Data and model notes

## Dataset provenance

`generate_training_data.py` creates `data/training_data.csv` with 5,000 **synthetically generated** examples by default: 1,000 each for `NORMAL`, `WARNING`, `BEARING_FAULT`, `OVERLOAD`, and `COOLING_FAULT`. It uses seeded random distributions to create plausible-looking educational examples. Generate the file before training; the generated CSV is not committed. These are not measurements from a real motor, factory, bearing, cooling system, or public industrial dataset.

The binary training target is `failure`: 0 for the generated normal group and 1 for the four generated abnormal/fault-pattern groups. The sensor feature columns are numeric; the text `machine_mode` is kept as metadata and is not used as a predictive-model input.

## Predictive-maintenance baseline

`train_model.py` trains a Random Forest classifier with a stratified 80/20 random holdout split and writes a model plus JSON metadata under `models/`. The metadata includes the split metrics, class counts, confusion matrix, and feature importance. The model estimates the synthetic binary label only. A model's `predict_proba` output is not automatically a calibrated real-world failure probability.

## Baseline result observed during this rebuild

Using `generate_training_data.py --seed 42` to create the 5,000-row synthetic dataset, the repository training script in the current test environment (NumPy 2.3.5, scikit-learn 1.8.0) produced 99.1% accuracy, 98.9% balanced accuracy, and 0.986 macro-F1 on one seeded 80/20 stratified split. The confusion matrix (true rows, predicted columns; labels 0 then 1) was `[[197, 3], [6, 794]]`. This is a reproducibility check on synthetic data generated from five predefined distributions. It is not a field-test result and must not be used as a claim of 99% accuracy on real industrial equipment.

## Anomaly baseline

`train_anomaly_model.py` fits a StandardScaler + IsolationForest pipeline using only rows labelled normal in the generated training set. It identifies readings that differ from that synthetic normal baseline. An anomaly does not prove a failure.

## Health score and RUL

The dashboard's sensor risk score is a transparent, rule-based screening index. When the predictive model is present, the dashboard displays the model estimate separately and blends it into the overall risk index. `health_score` is defined as 100 minus that risk index.

The displayed RUL is named `RUL proxy` deliberately. It is a simple illustrative heuristic; the project has no time-to-failure or run-to-failure labels, survival model, or field validation, so it is not a trained remaining-useful-life estimate.

## Before any industrial use

Replace the synthetic dataset with correctly labelled, machine-specific measured data; verify sensor calibration and scaling; split evaluation by machine/time/site to reduce leakage; evaluate precision, recall, false alarm rate, calibration and lead time; validate on a separate machine and operating regime; and review every action with qualified plant personnel. This academic prototype is not a safety controller, protection relay, or replacement for OEM alarms and maintenance procedures.
