# Scenario 3: Smart Agriculture
# Question:
# Developed an IOT system for monitoring soil moisture and temperature in a farm and send alerts to farmers
# when irrigation is needed.
# Programming focus:Sensors, Arduino/Raspberry Pi, Communication Protocols(e.g. LoRaWan, Sigfox), cloud platform
# (e.g. AWS IoT, Azure IoT), data visualization
# Question:
# Write a python script that reads data from a soil moisture sensor uses a machine learning model to predict irrigation
# needs and sends a notification to a user's mobile app.
# Programming focus: python, machine learning libraries(e.g. scikit-learn, tensorflow), sensor libraries, cloud services
# (e.g. AWS, Azure, Google Cloud)



import time
import json
import numpy as np
import requests
import pickle
import pandas as pd
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from firebase_admin import messaging
import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("path/to/firebase_credentials.json")
firebase_admin.initialize_app(cred)

iot_client = AWSIoTMQTTClient("smart_agriculture_client")
iot_client.configureEndpoint("your-aws-iot-endpoint.amazonaws.com", 8883)
iot_client.configureCredentials(
    "path/to/root-CA.pem", 
    "path/to/private.pem.key", 
    "path/to/certificate.pem.crt"
)
iot_client.configureOfflinePublishQueueing(-1)
iot_client.configureDrainingFrequency(2)
iot_client.configureConnectDisconnectTimeout(10)
iot_client.configureMQTTOperationTimeout(5)
iot_client.connect()

with open('irrigation_prediction_model.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

MOISTURE_THRESHOLD = 40
SENSOR_ID = "soil_sensor_1"
USER_DEVICE_TOKEN = "user_mobile_device_token"
FARM_LOCATION = "Field A"
SENSOR_TOPIC = f"farm/sensors/{SENSOR_ID}"
WEATHER_API_KEY = "your_weather_api_key"
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

sensor_history = []
HISTORY_LENGTH = 24

def get_weather_data(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "appid": WEATHER_API_KEY,
        "units": "metric"
    }
    response = requests.get(WEATHER_API_URL, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching weather data: {response.status_code}")
        return None

def send_notification(device_token, title, body):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=device_token,
    )
    
    try:
        response = messaging.send(message)
        print(f"Successfully sent notification: {response}")
        return True
    except Exception as e:
        print(f"Error sending notification: {e}")
        return False

def predict_irrigation_need(moisture, temperature, humidity, last_irrigation_hours, rainfall_last_24h):
    features = np.array([[moisture, temperature, humidity, last_irrigation_hours, rainfall_last_24h]])
    probability = model.predict_proba(features)[0][1]
    needs_irrigation = probability > 0.7
    return needs_irrigation, probability

def process_sensor_data(client, userdata, message):
    try:
        payload = json.loads(message.payload.decode('utf-8'))
        moisture = payload.get('moisture', 0)
        soil_temp = payload.get('soil_temperature', 0)
        timestamp = payload.get('timestamp', datetime.now().isoformat())
        print(f"Received sensor data - Moisture: {moisture}%, Soil Temp: {soil_temp}°C")
        
        weather_data = get_weather_data(lat=36.7783, lon=-119.4179)
        if weather_data:
            air_temp = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']
            rainfall = weather_data.get('rain', {}).get('1h', 0)
        else:
            air_temp = 25
            humidity = 50
            rainfall = 0
        
        last_irrigation_hours = 24
        
        data_point = {
            'timestamp': timestamp,
            'moisture': moisture,
            'soil_temp': soil_temp,
            'air_temp': air_temp,
            'humidity': humidity,
            'rainfall': rainfall
        }
        sensor_history.append(data_point)
        
        if len(sensor_history) > HISTORY_LENGTH:
            sensor_history.pop(0)
        
        rainfall_last_24h = sum(point['rainfall'] for point in sensor_history)
        
        irrigation_needed, confidence = predict_irrigation_need(
            moisture, soil_temp, humidity, last_irrigation_hours, rainfall_last_24h
        )
        
        if irrigation_needed:
            notification_title = "Irrigation Alert"
            notification_body = (
                f"Field {FARM_LOCATION} needs irrigation. "
                f"Current moisture: {moisture}%. "
                f"Confidence: {confidence*100:.1f}%"
            )
            send_notification(USER_DEVICE_TOKEN, notification_title, notification_body)
            print(f"Irrigation recommendation sent: {notification_body}")
        else:
            print(f"No irrigation needed. Moisture: {moisture}%, Confidence: {confidence*100:.1f}%")
        
        store_prediction_result(moisture, soil_temp, air_temp, humidity, rainfall_last_24h, irrigation_needed, confidence)
        
    except Exception as e:
        print(f"Error processing sensor data: {e}")

def store_prediction_result(moisture, soil_temp, air_temp, humidity, rainfall, irrigation_needed, confidence):
    result_data = {
        'timestamp': datetime.now().isoformat(),
        'sensor_id': SENSOR_ID,
        'location': FARM_LOCATION,
        'moisture': moisture,
        'soil_temperature': soil_temp,
        'air_temperature': air_temp,
        'humidity': humidity,
        'rainfall_24h': rainfall,
        'irrigation_needed': irrigation_needed,
        'prediction_confidence': confidence
    }
    
    iot_client.publish(
        topic="farm/analytics/irrigation_predictions",
        payload=json.dumps(result_data),
        qos=1
    )
    print("Prediction data stored to analytics pipeline")

def main():
    try:
        iot_client.subscribe(SENSOR_TOPIC, 1, process_sensor_data)
        print(f"Listening for sensor data on topic: {SENSOR_TOPIC}")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping smart irrigation system...")
    finally:
        iot_client.disconnect()
        print("Disconnected from AWS IoT")

if __name__ == "__main__":
    main()