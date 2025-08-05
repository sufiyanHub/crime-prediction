import json
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf
from datetime import datetime
import os
from datetime import datetime, timedelta
import random

app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "9856"


MODEL_FILE = "./model/conv_bilstm_autoencoder.h5"
ENCODER_LOCATION_FILE = "./model/location_encoder.pkl"
ENCODER_CRIME_FILE = "./model/crime_encoder.pkl"

if os.path.exists(MODEL_FILE):
    model = tf.keras.models.load_model(MODEL_FILE)
    le_location = joblib.load(ENCODER_LOCATION_FILE)
    le_crime = joblib.load(ENCODER_CRIME_FILE)
else:
    model = None
    le_location = None
    le_crime = None


def predict_crime(date, time, location, crime_type):
    if not model or not le_location or not le_crime:
        return None, "Model or encoders not loaded."

    try:
        datetime_input = pd.to_datetime(date + ' ' + time)
    except:
        return None, "Invalid date/time format. Use YYYY-MM-DD and HH:MM."

    if location not in le_location.classes_:
        return None, f"Location '{location}' not found in training data."

    if crime_type not in le_crime.classes_:
        return None, f"Crime type '{crime_type}' not found in training data."
    
    month = datetime_input.month
    day = datetime_input.day
    weekday = datetime_input.weekday()
    hour = datetime_input.hour

    location_encoded = le_location.transform([location])[0]
    crime_encoded = le_crime.transform([crime_type])[0]

    input_data = np.array([
        location_encoded, crime_encoded, month, day, weekday, hour
    ]).reshape(1, 6, 1)

    predicted_rate = model.predict(input_data)[0][0]

    return predicted_rate, None



@app.route('/predict', methods=['GET'])
def predict():
    return render_template("details.html")
@app.route('/predict', methods=['POST'])
def get_crime_prediction():
    if request.is_json:
        data = request.get_json()
        location = data.get('location')
        datetime_str = data.get('datetime')
        crime_type = data.get('crime_type')
    else:
        location = request.form.get('area')
        date = request.form.get('date')
        time = request.form.get('time')
        crime_type = request.form.get('crime')
        datetime_str = f"{date} {time}"

    if not location or not datetime_str or not crime_type:
        return jsonify({"success": False, "message": "Missing input data."}), 400

    date, time = datetime_str.split(' ')
    prediction = 0
    prediction, error = predict_crime(date, time, location, crime_type)
    daily_data = generate_daily_data(date,time,location,crime_type) 
    if error:
        return jsonify({"success": False, "message": error}), 400
    print(prediction)
    crimePred = {'crime': crime_type, 'location': location, 'date': date, 'time': time, 'prediction': float(prediction[0]), 'daily':daily_data}
    return render_template('result.html', crime_pred=json.dumps(crimePred))



from datetime import datetime, timedelta

def generate_daily_data(start_date,time, location, crime_type):
    current_date = datetime.strptime(start_date, '%Y-%m-%d')
    daily_data = []

    for i in range(30, 0, -1):
        date = (current_date - timedelta(days=i)).strftime('%Y-%m-%d')
        crime_rate, _ = predict_crime(date, time, location, crime_type)
        daily_data.append({
            'date': date,
            'crime_rate': float(crime_rate) * 100
        })

    return daily_data


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/login", methods=["GET"])
def loginPage():
    return render_template("login.html")


@app.route("/signup", methods=["GET"])
def signupPage():
    return render_template("signup.html")


if __name__ == "__main__":
    print("Server running at: http://127.0.0.1:5000/")
    app.run(host="0.0.0.0", port=5000, debug=True)