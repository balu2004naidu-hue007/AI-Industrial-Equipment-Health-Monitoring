# System architecture

```text
Arduino / USB serial sensor gateway       Laptop demo simulator
                |                                  |
                +------------ CSV records ---------+
                               |
                               v
                    data/live_machine_data.csv
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
       Shared validation + analysis     Browser dashboard
                 |                       /api/live (local)
         +-------+--------+
         |                |
         v                v
   Random Forest     Isolation Forest
   binary baseline  anomaly baseline
         |                |
         +-------+--------+
                 v
       risk / health / advice
```

The CSV file is the shared interface between data acquisition and the dashboard. The serial logger and simulator write the same schema; the dashboard reads it again every two seconds. The model-training scripts produce local model files. If model files are absent, the dashboard can still show the rule-based sensor risk score and explicitly indicates that the predictive model is unavailable.

The HTTP server binds to `127.0.0.1` by default. Keep it local unless you understand the network and access-control implications of exposing a development dashboard.
