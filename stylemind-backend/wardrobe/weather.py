# # wardrobe/weather.py
# import os
# import requests

# OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# def get_weather(city):
#     url = "https://api.openweathermap.org/data/2.5/weather"
#     params = {"q": city, "appid": OPENWEATHER_API_KEY, "units": "metric"}
#     response = requests.get(url, params=params, timeout=5)
#     response.raise_for_status()
#     data = response.json()
#     return {
#         "city": data.get("name", city),
#         "country": data.get("sys", {}).get("country"),
#         "temp_c": data["main"]["temp"],
#         "feels_like_c": data["main"].get("feels_like"),
#         "description": data["weather"][0]["description"] if data.get("weather") else None,
#         "humidity": data["main"].get("humidity"),
#     }

# def get_current_temp(city):
#     return get_weather(city)["temp_c"]

# # ===================== CHANGE START =====================
# # NEW — same shape as get_weather(), but looks up by GPS coordinates
# # instead of a city name string. OpenWeather supports lat/lon directly on
# # the same endpoint, so no separate reverse-geocoding step is needed.
# def get_weather_by_coords(lat, lon):
#     url = "https://api.openweathermap.org/data/2.5/weather"
#     params = {"lat": lat, "lon": lon, "appid": OPENWEATHER_API_KEY, "units": "metric"}
#     response = requests.get(url, params=params, timeout=5)
#     response.raise_for_status()
#     data = response.json()
#     return {
#         "city": data.get("name"),  # OpenWeather resolves the nearest city name for these coords
#         "country": data.get("sys", {}).get("country"),
#         "temp_c": data["main"]["temp"],
#         "feels_like_c": data["main"].get("feels_like"),
#         "description": data["weather"][0]["description"] if data.get("weather") else None,
#         "humidity": data["main"].get("humidity"),
#     }

# # NEW — single shared resolution order used by BOTH /api/recommend/ and
# # the chatbot, so the "which weather source wins" logic only lives in one
# # place: typed city > GPS coordinates > manual/fallback temperature.
# # Returns (temp_c, weather_info_or_None). Raises ValueError if nothing
# # could be resolved at all (only possible if manual_temp is also None).
# def resolve_temperature(city=None, lat=None, lon=None, manual_temp=None):
#     if city:
#         try:
#             w = get_weather(city)
#             return w["temp_c"], w
#         except Exception:
#             pass  # bad city name, network issue, etc. — fall through to GPS or manual

#     if lat is not None and lon is not None:
#         try:
#             w = get_weather_by_coords(lat, lon)
#             return w["temp_c"], w
#         except Exception:
#             pass  # fall through to manual

#     if manual_temp is not None:
#         return float(manual_temp), None

#     raise ValueError("Could not determine temperature — provide a city, allow location access, or set a manual temperature.")
# # ===================== CHANGE END =====================



# # wardrobe/weather.py
# import os
# import requests

# OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# # Reverse-geocodes coordinates to a broader province/state name — this
# # part was already working correctly, so it stays on OpenWeatherMap's
# # geocoding endpoint (a different, unrelated service from their actual
# # weather data, which is what was inaccurate).
# def get_region_by_coords(lat, lon):
#     url = "http://api.openweathermap.org/geo/1.0/reverse"
#     params = {"lat": lat, "lon": lon, "limit": 1, "appid": OPENWEATHER_API_KEY}
#     response = requests.get(url, params=params, timeout=5)
#     response.raise_for_status()
#     results = response.json()
#     if not results:
#         return None
#     place = results[0]
#     return place.get("name") or place.get("state")


# # ===================== CHANGE START =====================
# # NEW — Open-Meteo's numeric weather codes (WMO standard) need mapping to
# # human-readable text, since unlike OpenWeatherMap it doesn't return a
# # description string directly.
# WEATHER_CODE_DESCRIPTIONS = {
#     0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
#     45: "fog", 48: "depositing rime fog",
#     51: "light drizzle", 53: "moderate drizzle", 55: "dense drizzle",
#     61: "slight rain", 63: "moderate rain", 65: "heavy rain",
#     71: "slight snow", 73: "moderate snow", 75: "heavy snow",
#     80: "slight rain showers", 81: "moderate rain showers", 82: "violent rain showers",
#     95: "thunderstorm", 96: "thunderstorm with hail", 99: "severe thunderstorm with hail",
# }


# # CHANGED — now fetches actual weather from Open-Meteo instead of
# # OpenWeatherMap, since it blends multiple weather models rather than a
# # single nearest-station reading, and is generally noticeably more
# # accurate, especially outside major cities. No API key required.
# def get_weather_by_coords(lat, lon):
#     url = "https://api.open-meteo.com/v1/forecast"
#     params = {
#         "latitude": lat,
#         "longitude": lon,
#         "current": "temperature_2m,relative_humidity_2m,apparent_temperature,weather_code",
#         "timezone": "auto",
#     }
#     response = requests.get(url, params=params, timeout=5)
#     response.raise_for_status()
#     data = response.json()
#     current = data["current"]

#     try:
#         region = get_region_by_coords(lat, lon)
#     except Exception:
#         region = None

#     weather_code = current.get("weather_code")
#     description = WEATHER_CODE_DESCRIPTIONS.get(weather_code, "unknown conditions")

#     return {
#         "city": region,
#         "country": None,  # Open-Meteo's /forecast endpoint doesn't return a country code
#         "temp_c": current["temperature_2m"],
#         "feels_like_c": current.get("apparent_temperature"),
#         "description": description,
#         "humidity": current.get("relative_humidity_2m"),
#     }
# # ===================== CHANGE END =====================


# def resolve_temperature(lat=None, lon=None, manual_temp=None):
#     if lat is not None and lon is not None:
#         try:
#             w = get_weather_by_coords(lat, lon)
#             return w["temp_c"], w
#         except Exception:
#             pass

#     if manual_temp is not None:
#         return float(manual_temp), None

#     raise ValueError("Could not determine temperature — allow location access or set a manual temperature.")



# wardrobe/weather.py
import os
import requests
from django.core.cache import cache  # ===================== CHANGE START =====================

WEATHERAPI_KEY = os.environ.get("WEATHERAPI_KEY")

def get_weather_by_coords(lat, lon):
    # ===================== CHANGE START =====================
    # NEW — cache results for 15 minutes, keyed by rounded coordinates.
    # Rounding to 2 decimal places (~1.1km precision) means nearby repeat
    # requests (e.g. clicking "Generate New" a few times in a row) hit the
    # cache instead of calling the paid/rate-limited API again — faster
    # responses, fewer calls, and comfortably within the free tier's quota.
    cache_key = f"weather:{round(float(lat), 2)}:{round(float(lon), 2)}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached
    # ===================== CHANGE END =====================

    url = "https://api.weatherapi.com/v1/current.json"
    params = {"key": WEATHERAPI_KEY, "q": f"{lat},{lon}", "aqi": "no"}
    response = requests.get(url, params=params, timeout=5)
    response.raise_for_status()
    data = response.json()
    location = data.get("location", {})
    current = data.get("current", {})
    result = {
        "location_name": location.get("name"),
        "region": location.get("region"),
        "country": location.get("country"),
        "temp_c": current.get("temp_c"),
        "feels_like_c": current.get("feelslike_c"),
        "description": current.get("condition", {}).get("text"),
        "humidity": current.get("humidity"),
        "precip_mm": current.get("precip_mm"),   # NEW — needed for the rain-aware nudge
    }

    # ===================== CHANGE START =====================
    # NEW — store this result for 15 minutes (900 seconds) before it's
    # considered stale and a fresh API call is made again
    cache.set(cache_key, result, timeout=900)
    # ===================== CHANGE END =====================

    return result


def resolve_temperature(lat=None, lon=None, manual_temp=None):
    if lat is not None and lon is not None:
        try:
            w = get_weather_by_coords(lat, lon)
            return w["temp_c"], w
        except Exception as e:
            print(f"[weather] get_weather_by_coords failed: {e}")
    if manual_temp is not None:
        return float(manual_temp), None
    raise ValueError("Could not determine temperature — allow location access or set a manual temperature.")

# ===================== CHANGE START =====================
# NEW — rain-aware nudge. Purely informational (icon + short text), not a
# filtering signal — the actual outfit filtering in filtering.py stays
# temperature-only, per the earlier decision to keep rain out of item
# selection for now. This just tells the user "bring an umbrella" on top
# of whatever outfit gets recommended.
RAIN_KEYWORDS = ["rain", "drizzle", "shower", "thunderstorm"]


def get_rain_nudge(weather_info):
    """
    Returns {"icon": "umbrella", "message": ...} if the current weather
    looks rainy, or None if it doesn't / weather_info is unavailable
    (e.g. user set a manual temp with no live weather lookup).

    Combines two signals since either alone can miss real rain:
      - precip_mm > 0: actual measured precipitation this reading
      - condition description containing a rain-related keyword: catches
        "light rain" / "patchy rain possible" even when precip_mm hasn't
        registered anything yet
    """
    if not weather_info:
        return None

    precip_mm = weather_info.get("precip_mm") or 0
    description = (weather_info.get("description") or "").lower()

    is_rainy = precip_mm > 0 or any(keyword in description for keyword in RAIN_KEYWORDS)

    if not is_rainy:
        return None

    return {
        "icon": "umbrella",
        "message": "Looks like rain — consider grabbing an umbrella or raincoat.",
    }
# ===================== CHANGE END =====================