# Arduino / serial integration

The uploaded project archive did **not** include an Arduino sketch, sensor list, pin map, or wiring diagram. This folder therefore documents the serial contract but does not invent sensor connections.

The Python logger expects one comma-separated line per reading at 9600 baud by default:

```text
temperature,vibration,rpm,motor_current,voltage,power,pressure,ambient_temperature,load,running_hours,machine_mode
```

Example **test payload only** (not measured hardware values):

```text
72.5,4.8,1480,7.0,224,1568,2.35,29,75,681.2,WARNING
```

The final `machine_mode` value is optional. When it is absent, the logger uses `--default-mode NORMAL` unless another allowed mode is selected. The ten numeric values must be sent in the documented order.

Before wiring real hardware, confirm each sensor's output type, operating range, signal conditioning, isolation, supply voltage, ADC range, and engineering-unit conversion from its datasheet. Update the serial producer only after the actual sensor/module details and pin mapping are known. Do not connect industrial mains or motor-drive signals directly to a microcontroller input.
