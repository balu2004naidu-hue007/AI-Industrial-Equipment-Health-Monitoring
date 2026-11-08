# Serial data protocol

## Transport

- Default baud rate: `9600` baud, 8 data bits, no parity, 1 stop bit (pySerial default).
- One CSV record per line, terminated by newline.
- Default serial port is `COM3` on Windows; override with `--port COMx`.
- Numeric fields must be finite decimal numbers. The final mode token is optional.

## Field order

| Index | Field | Display unit | Required | Notes |
|---:|---|---|---|---|
| 1 | `temperature` | °C | Yes | Machine temperature sensor, with suitable conditioning |
| 2 | `vibration` | mm/s (assumed) | Yes | Confirm whether the sensor reports RMS, peak, or raw acceleration |
| 3 | `rpm` | rev/min | Yes | Motor/shaft speed |
| 4 | `motor_current` | A | Yes | Use a suitably rated isolated current sensor/transducer |
| 5 | `voltage` | V | Yes | Use an appropriately isolated voltage transducer |
| 6 | `power` | W | Yes | If sent as zero while voltage and current are positive, software estimates V×I |
| 7 | `pressure` | bar (assumed) | Yes | Confirm sensor range and units |
| 8 | `ambient_temperature` | °C | Yes | Ambient temperature |
| 9 | `load` | % | Yes | Project-defined load percentage; document its source/calibration |
| 10 | `running_hours` | h | Yes | Cumulative operating time |
| 11 | `machine_mode` | enum | Optional | `NORMAL`, `WARNING`, `BEARING_FAULT`, `OVERLOAD`, `COOLING_FAULT` |

Example:

```text
72.5,4.8,1480,7.0,224,1568,2.35,29,75,681.2,WARNING
```

Ten numeric fields without the final mode are also accepted. In that case, set a default with `--default-mode`. Invalid, non-finite, out-of-range, or incorrectly sized records are skipped and reported; they are not written into the CSV.

The logger appends to `data/live_machine_data.csv` using this exact header:

```text
timestamp,temperature,vibration,rpm,motor_current,voltage,power,pressure,ambient_temperature,load,running_hours,machine_mode
```

If an existing CSV has a different header, the logger stops rather than silently replacing historical data.
