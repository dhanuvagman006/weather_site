from flask import Flask, render_template, request, redirect, url_for
from flask_cors import CORS
import requests
import os
from dotenv import load_dotenv
from functools import lru_cache
from datetime import datetime, timedelta
import json


load_dotenv()
file_path = 'users.json'

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["http://localhost:5000", "http://127.0.0.1:5000"]}})

API_KEY = os.getenv('OPENWEATHER_API_KEY')
if not API_KEY:
    raise ValueError("OPENWEATHER_API_KEY environment variable is not set")

BASE_URL = "https://api.openweathermap.org/data/2.5"

@lru_cache(maxsize=100)
def cached_weather_request(url, timeout=5):
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()

def load_users():
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                return data.get('users', [])
            except json.JSONDecodeError:
                return []
    return []

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if not email or not password:
            return ("<h1>Cannot Have Empty Emails and Password</h1>")

        users = load_users()
        for user in users:
            if user['email'] == email and user['password'] == password:
                return redirect(url_for('dashboard'))

        return "Invalid email or password", 401

    return render_template('Loginpage.html')

@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        user_data = {
            "name": request.form['name'],
            "email": request.form['email'],
            "phone": request.form['phone'],
            "password": request.form['password']
        }
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                try:
                    data = json.load(f)
                    if not isinstance(data, dict):
                        data = {"users": []}
                except json.JSONDecodeError:
                    data = {"users": []}
        else:
            data = {"users": []}

        data['users'].append(user_data)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

        return redirect(url_for('success'))

    return render_template('Register.html')

@app.route('/success')
def success():
    return render_template('Success.html')

@app.route('/dashboard')
def dashboard():
    return render_template('Homepage.html')

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/get-weather')
def get_weather():
    city = request.args.get('city')
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not (city or (lat and lon)):
        return jsonify({'cod': 400, 'message': 'City or coordinates required'}), 400

    try:
        if city:
            url = f"{BASE_URL}/weather?q={city.strip()}&appid={API_KEY}&units=metric"
        else:
            url = f"{BASE_URL}/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
        
        data = cached_weather_request(url)
        
        if data.get('cod') != 200:
            return jsonify({'cod': data.get('cod'), 'message': data.get('message')}), 404

        return jsonify({
            'cod': 200,
            'name': data['name'],
            'description': data['weather'][0]['description'],
            'icon': data['weather'][0]['icon'],
            'temp': round(data['main']['temp'], 1),
            'humidity': data['main']['humidity'],
            'wind_speed': round(data['wind']['speed'], 1),
            'lat': data['coord']['lat'],
            'lon': data['coord']['lon']
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'cod': 500, 'message': f'Failed to fetch weather data: {str(e)}'}), 500

@app.route('/get-forecast')
def get_forecast():
    city = request.args.get('city')
    
    if not city:
        return jsonify({'cod': 400, 'message': 'City parameter is required'}), 400

    try:
        url = f"{BASE_URL}/forecast?q={city.strip()}&appid={API_KEY}&units=metric"
        data = cached_weather_request(url)

        if data.get('cod') != '200':
            return jsonify({'cod': data.get('cod'), 'message': data.get('message')}), 404

        forecast_list = [
            {
                'dt_txt': item['dt_txt'],
                'temp': round(item['main']['temp'], 1),
                'description': item['weather'][0]['description'],
                'icon': item['weather'][0]['icon']
            }
            for item in data['list']
        ]

        return jsonify({
            'cod': 200,
            'city': data['city']['name'],
            'forecast': forecast_list
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'cod': 500, 'message': f'Failed to fetch forecast data: {str(e)}'}), 500

@app.route('/get-weekly-forecast')
def get_weekly_forecast():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    
    if not (lat and lon):
        return jsonify({'cod': 400, 'message': 'Coordinates required'}), 400

    try:
        today = datetime.now().strftime('%Y-%m-%d')
        next_week = (datetime.now() + timedelta(days=6)).strftime('%Y-%m-%d')
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto&start_date={today}&end_date={next_week}"
        data = cached_weather_request(url)

        if not data.get('daily'):
            return jsonify({'cod': 404, 'message': 'No forecast data available'}), 404

        weather_icons = {
            0: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/clear-day.svg",
            1: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/mostly-clear-day.svg",
            2: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/partly-cloudy-day.svg",
            3: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/cloudy.svg",
            45: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/fog.svg",
            48: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/fog.svg",
            51: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/drizzle.svg",
            61: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/rain.svg",
            71: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/snow.svg",
            80: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/showers-day.svg",
            95: "https://cdn.jsdelivr.net/gh/basmilius/weather-icons/production/fill/all/thunderstorms.svg",
        }

        forecast = [
            {
                'day': datetime.strptime(date, '%Y-%m-%d').strftime('%a'),
                'max_temp': round(data['daily']['temperature_2m_max'][i], 1),
                'min_temp': round(data['daily']['temperature_2m_min'][i], 1),
                'icon': weather_icons.get(data['daily']['weathercode'][i], weather_icons[3])
            }
            for i, date in enumerate(data['daily']['time'])
        ]

        return jsonify({
            'cod': 200,
            'forecast': forecast
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'cod': 500, 'message': f'Failed to fetch weekly forecast: {str(e)}'}), 500

@app.route('/get-city-suggestions')
def get_city_suggestions():
    query = request.args.get('query')
    
    if not query or len(query) < 3:
        return jsonify({'cod': 400, 'message': 'Query must be at least 3 characters'}), 400

    try:
        url = f"http://api.openweathermap.org/geo/1.0/direct?q={query}&limit=5&appid={API_KEY}"
        data = cached_weather_request(url)

        cities = [f"{item['name']}, {item['country']}" for item in data]
        return jsonify({
            'cod': 200,
            'cities': cities
        })

    except requests.exceptions.RequestException as e:
        return jsonify({'cod': 500, 'message': f'Failed to fetch city suggestions: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)