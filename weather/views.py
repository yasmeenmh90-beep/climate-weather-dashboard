import requests
from django.shortcuts import render

API_KEY = "c0e380f1b4d6996639d2a61d48d49c92"

def get_aqi_label(aqi):
    labels = {1: "Good 🟢", 2: "Fair 🟡", 3: "Moderate 🟠", 4: "Poor 🔴", 5: "Very Poor 🟣"}
    return labels.get(aqi, "Unknown")

def get_weather_advice(temp, humidity, wind_speed, aqi, description):
    advice = []
    score = 100

    if aqi >= 4:
        advice.append("⚠️ Air quality is poor — avoid outdoor activities!")
        score -= 40
    elif aqi == 3:
        advice.append("😷 Moderate air quality — sensitive people should be cautious.")
        score -= 20

    if "rain" in description.lower() or "storm" in description.lower():
        advice.append("🌧️ Rain expected — carry an umbrella!")
        score -= 20
    elif "snow" in description.lower():
        advice.append("❄️ Snow expected — dress warmly and drive carefully!")
        score -= 25

    if temp > 38:
        advice.append("🥵 Extreme heat — stay hydrated and avoid midday sun!")
        score -= 20
    elif temp > 30:
        advice.append("☀️ Hot day — stay hydrated!")
        score -= 10
    elif temp < 5:
        advice.append("🥶 Very cold — wear warm clothes!")
        score -= 15

    if wind_speed > 10:
        advice.append("💨 Strong winds — secure loose items!")
        score -= 10

    if humidity > 85:
        advice.append("💧 Very humid — may feel uncomfortable outside.")
        score -= 10

    score = max(0, score)

    if score >= 80:
        overall = "✅ Great day to go outside!"
    elif score >= 60:
        overall = "👍 Decent day — take some precautions."
    elif score >= 40:
        overall = "⚠️ Be cautious if going outside."
    else:
        overall = "❌ Stay indoors if possible!"

    if not advice:
        advice.append("😊 Weather looks good — enjoy your day!")

    return {"overall": overall, "tips": advice, "score": score}

def index(request):
    weather_data = None
    forecast_data = None
    aqi_data = None
    advice = None
    error = None
    city = request.GET.get("city", "Dubai")

    try:
        # Current weather
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            error = f"City '{city}' not found!"
        else:
            lat = data["coord"]["lat"]
            lon = data["coord"]["lon"]

            weather_data = {
                "city": data["name"],
                "country": data["sys"]["country"],
                "temp": round(data["main"]["temp"]),
                "feels_like": round(data["main"]["feels_like"]),
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
                "description": data["weather"][0]["description"].title(),
                "icon": data["weather"][0]["icon"],
                "pressure": data["main"]["pressure"],
                "visibility": data.get("visibility", 0) // 1000,
            }

            # AQI
            aqi_url = f"https://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
            aqi_response = requests.get(aqi_url)
            aqi_json = aqi_response.json()
            aqi_value = aqi_json["list"][0]["main"]["aqi"]
            components = aqi_json["list"][0]["components"]
            aqi_data = {
                "aqi": aqi_value,
                "label": get_aqi_label(aqi_value),
                "pm2_5": round(components.get("pm2_5", 0), 1),
                "pm10": round(components.get("pm10", 0), 1),
                "co": round(components.get("co", 0), 1),
                "no2": round(components.get("no2", 0), 1),
            }

            # AI Advice
            advice = get_weather_advice(
                weather_data["temp"],
                weather_data["humidity"],
                weather_data["wind_speed"],
                aqi_value,
                weather_data["description"]
            )

            # Forecast
            forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={API_KEY}&units=metric&cnt=5"
            forecast_response = requests.get(forecast_url)
            forecast_json = forecast_response.json()

            if forecast_json.get("cod") == "200":
                forecast_data = []
                for item in forecast_json["list"]:
                    forecast_data.append({
                        "time": item["dt_txt"],
                        "temp": round(item["main"]["temp"]),
                        "description": item["weather"][0]["description"].title(),
                        "icon": item["weather"][0]["icon"],
                    })

    except Exception as e:
        error = "Could not fetch weather data. Please try again."

    return render(request, "weather/index.html", {
        "weather": weather_data,
        "forecast": forecast_data,
        "aqi": aqi_data,
        "advice": advice,
        "error": error,
        "city": city,
    })

def compare(request):
    cities = request.GET.getlist("city")
    cities_data = []

    for city in cities[:3]:
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"
            response = requests.get(url)
            data = response.json()
            if data.get("cod") == 200:
                cities_data.append({
                    "city": data["name"],
                    "country": data["sys"]["country"],
                    "temp": round(data["main"]["temp"]),
                    "humidity": data["main"]["humidity"],
                    "wind_speed": data["wind"]["speed"],
                    "description": data["weather"][0]["description"].title(),
                    "icon": data["weather"][0]["icon"],
                })
        except:
            pass

    return render(request, "weather/compare.html", {"cities": cities_data})