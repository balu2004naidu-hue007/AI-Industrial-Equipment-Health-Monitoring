import serial
import csv
import time
from datetime import datetime
import joblib
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

# Load AI model
model = joblib.load("models/model.pkl")

# Connect to Arduino
arduino = serial.Serial("COM3", 9600, timeout=1)
time.sleep(2)

# Open CSV file
with open("dataset/machine_log.csv", "a", newline="") as file:

    writer = csv.writer(file)

    # Write header if file is empty
    if file.tell() == 0:
        writer.writerow([
            "Time",
            "Temperature",
            "Vibration",
            "RPM",
            "Failure"
        ])

    print("Receiving live data...")

    while True:

        try:
            # Read serial data
            data = arduino.readline().decode(errors="ignore").strip()

            if data == "":
                continue

            print("Received:", data)

            parts = data.split(",")

            if len(parts) != 3:
                continue

            temp = int(parts[0])
            vib = int(parts[1])
            rpm = int(parts[2])

            # Create DataFrame for prediction
            sample = pd.DataFrame({
                "Temperature": [temp],
                "Vibration": [vib],
                "RPM": [rpm]
            })

            # AI Prediction
            prediction = model.predict(sample)
            failure = int(prediction[0])

            # Save to CSV
            writer.writerow([
                datetime.now(),
                temp,
                vib,
                rpm,
                failure
            ])

            file.flush()

            # Print status
            status = "🟢 Healthy"

            if failure == 1:
                status = "🔴 Maintenance Required"

            print("--------------------------------")
            print(f"Temperature : {temp}")
            print(f"Vibration   : {vib}")
            print(f"RPM         : {rpm}")
            print(f"Status      : {status}")

        except Exception as e:
            print("Prediction Error:", e)
            continue