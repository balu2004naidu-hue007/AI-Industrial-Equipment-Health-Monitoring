# Data directory

- `sample_live_data.csv` is a short generated serial/dashboard example. Its values are illustrative, not real machine measurements.
- `training_data.csv` is generated locally by `python generate_training_data.py` (5,000 synthetic rows by default). It is not committed as an observed dataset.
- `live_machine_data.csv`, `prediction_results.csv`, and JSON reports are created at runtime by the simulator, serial logger, and analysis scripts; they are ignored by Git.

Always identify synthetic/demo data clearly when showing project screenshots or results.
