import pandas as pd
import joblib
import csv
from datetime import datetime
import time

# Load trained model
model = joblib.load("models/model.pkl")

print("AI Prediction Started...\n")

while True:
    # Read latest machine data
    df = pd.read_csv("dataset/machine_log.csv")

    latest = df.iloc[-1]

    temp = int(latest["Temperature"])
    vib = int(latest["Vibration"])
    rpm = int(latest["RPM"])

    # AI Prediction
    prediction = model.predict([[temp, vib, rpm]])

    if prediction[0] == 0:
        status = "Machine Healthy"
    else:
        status = "Maintenance Required"

    print("--------------------------------")
    print(f"Temperature : {temp} °C")
    print(f"Vibration   : {vib}")
    print(f"RPM         : {rpm}")
    print(f"Status      : {status}")

    # Save prediction history
    with open("dataset/prediction_history.csv", "a", newline="") as file:
        writer = csv.writer(file)

        if file.tell() == 0:
            writer.writerow(["Time", "Temperature", "Vibration", "RPM", "Prediction"])

        writer.writerow([
            datetime.now(),
            temp,
            vib,
            rpm,
            status
        ])

    time.sleep(2)