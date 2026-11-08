from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from generate_training_data import generate_dataset
from industrial_monitoring.training import train_anomaly_model, train_predictive_model


def test_generator_has_balanced_documented_modes():
    frame = generate_dataset(samples_per_mode=25, seed=4)
    assert len(frame) == 125
    assert frame["machine_mode"].value_counts().to_dict() == {
        "NORMAL": 25, "WARNING": 25, "BEARING_FAULT": 25, "OVERLOAD": 25, "COOLING_FAULT": 25
    }
    assert frame.groupby("machine_mode")["failure"].first().to_dict() == {
        "NORMAL": 0, "WARNING": 1, "BEARING_FAULT": 1, "OVERLOAD": 1, "COOLING_FAULT": 1
    }


def test_trainers_write_models_and_metadata(tmp_path):
    data_file = tmp_path / "training.csv"
    generate_dataset(samples_per_mode=60, seed=10).to_csv(data_file, index=False)
    models_dir = tmp_path / "models"
    metrics = train_predictive_model(data_file, models_dir, random_state=11)
    anomaly = train_anomaly_model(data_file, models_dir, random_state=11)
    assert 0 <= metrics["metrics"]["accuracy"] <= 1
    assert metrics["training_data_is_synthetic"] is True
    assert (models_dir / "predictive_maintenance_model.joblib").is_file()
    assert (models_dir / "predictive_metadata.json").is_file()
    assert anomaly["training_rows"] == 60
    assert (models_dir / "anomaly_detection_model.joblib").is_file()
    assert (models_dir / "anomaly_metadata.json").is_file()
