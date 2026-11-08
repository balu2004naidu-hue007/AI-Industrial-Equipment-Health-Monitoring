# Generated models

Model binaries are intentionally not committed. Generate locally with:

```bash
python train_model.py
python train_anomaly_model.py
```

The scripts create `predictive_maintenance_model.joblib`, `anomaly_detection_model.joblib`, and JSON metadata files in this directory. Joblib files use Python pickle serialization; only load model files produced by your own trusted training run.
