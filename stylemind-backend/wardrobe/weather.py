import os
import requests

OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

def get_current_temp(city):
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    data = response.json()
    return data["main"]["temp"]