"""
weather.py — a shared current-conditions helper.

Several apps want "the weather right now". Rather than each hardcoding a provider
and key, this resolves the *global* weather settings (provider + API key +
location) and returns one normalized current-conditions dict. The plugin runtime
injects it into any app whose ``fetch()`` opts in with a ``get_weather``
parameter (see app.py); the app calls ``get_weather()`` and renders the
result, so switching providers is a global setting, not an app edit.

Providers: Open-Meteo (keyless — the default, so weather works with no API key),
OpenWeather, WeatherAPI and QWeather (each keyed via the global weather_api_key).
Temperatures are normalized to Fahrenheit; the caller formats/converts.

Uses the blocking ``requests`` library (already a project dependency); a small
client shim gives every request a default timeout.
"""

from __future__ import annotations

import logging
import time

import requests

import location

log = logging.getLogger("splitflap.weather")

# Short-TTL cache so the provider is hit at most once per location per window,
# regardless of how many apps call get_weather() or how often they refresh.
_CACHE_TTL = 600  # seconds
_cache: dict = {}   # (provider, key, lat, lon) -> (fetched_at, data)

# Global settings the helper consumes — so the UI can credit weather-using apps
# under these settings even though they read them via get_weather, not directly.
GLOBAL_KEYS = ("weather_provider", "weather_api_key", "zip_code", "location_precise")

# Compact Open-Meteo WMO weather-code → text map (current conditions only).
_OPENMETEO_CODES = {
    0: "CLEAR", 1: "MAINLY CLEAR", 2: "PARTLY CLOUDY", 3: "OVERCAST",
    45: "FOG", 48: "RIME FOG", 51: "LIGHT DRIZZLE", 53: "DRIZZLE", 55: "HEAVY DRIZZLE",
    56: "FREEZING DRIZZLE", 57: "FREEZING DRIZZLE", 61: "LIGHT RAIN", 63: "RAIN",
    65: "HEAVY RAIN", 66: "FREEZING RAIN", 67: "FREEZING RAIN", 71: "LIGHT SNOW",
    73: "SNOW", 75: "HEAVY SNOW", 77: "SNOW GRAINS", 80: "RAIN SHOWERS",
    81: "RAIN SHOWERS", 82: "HEAVY SHOWERS", 85: "SNOW SHOWERS", 86: "HEAVY SNOW SHOWERS",
    95: "THUNDERSTORM", 96: "THUNDER HAIL", 99: "SEVERE TSTORM",
}


class _Client:
    """Minimal requests-backed stand-in for httpx.Client: a session that applies a
    default timeout to every ``get()`` so the provider helpers stay unchanged."""

    def __init__(self, timeout=8.0):
        self._session = requests.Session()
        self._timeout = timeout

    def get(self, url, params=None, headers=None):
        return self._session.get(url, params=params, headers=headers, timeout=self._timeout)

    def close(self):
        self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def _i(v):
    try:
        return int(round(float(v)))
    except (TypeError, ValueError):
        return None


# Boston, so weather always has something to show if no location is configured.
_FALLBACK_LOCATION = (42.3496, -71.0783, "BOSTON")


def _resolve_location(settings):
    """(lat, lon, city) for the configured location via the shared geocoder in
    location.py (cached, one Nominatim lookup for weather + get_location), with a
    Boston fallback so weather is never blank."""
    return location.coordinates(settings) or _FALLBACK_LOCATION


def _openmeteo(client, lat, lon, city, _key):
    d = client.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": lat, "longitude": lon,
        "current": "temperature_2m,apparent_temperature,weather_code,"
                   "relative_humidity_2m,wind_speed_10m,cloud_cover",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit", "wind_speed_unit": "mph",
        "timezone": "auto", "forecast_days": 1,
    }).json()
    cur = d.get("current", {})
    daily = d.get("daily", {})
    hi = (daily.get("temperature_2m_max") or [cur.get("temperature_2m")])[0]
    lo = (daily.get("temperature_2m_min") or [cur.get("temperature_2m")])[0]
    code = cur.get("weather_code")
    return {
        "city": city, "temp_f": _i(cur.get("temperature_2m")),
        "feels_like_f": _i(cur.get("apparent_temperature")),
        "hi_f": _i(hi), "lo_f": _i(lo),
        "desc": _OPENMETEO_CODES.get(code, "CURRENT CONDITIONS"), "code": code,
        "humidity": _i(cur.get("relative_humidity_2m")),
        "wind_mph": cur.get("wind_speed_10m"), "cloud_cover": _i(cur.get("cloud_cover")),
    }


def _openweather(client, lat, lon, city, key):
    d = client.get("https://api.openweathermap.org/data/2.5/weather", params={
        "lat": lat, "lon": lon, "appid": key, "units": "imperial",
    }).json()
    main = d.get("main", {})
    return {
        "city": str(d.get("name", city)).upper(), "temp_f": _i(main.get("temp")),
        "feels_like_f": _i(main.get("feels_like")),
        "hi_f": _i(main.get("temp_max")), "lo_f": _i(main.get("temp_min")),
        "desc": str((d.get("weather") or [{}])[0].get("main", "CURRENT CONDITIONS")).upper(),
        "code": None, "humidity": _i(main.get("humidity")),
        "wind_mph": (d.get("wind") or {}).get("speed"),
        "cloud_cover": _i((d.get("clouds") or {}).get("all")),
    }


def _weatherapi(client, lat, lon, city, key):
    d = client.get("https://api.weatherapi.com/v1/forecast.json", params={
        "key": key, "q": f"{lat},{lon}", "days": 1,
    }).json()
    cur = d.get("current", {})
    day = ((d.get("forecast") or {}).get("forecastday") or [{}])[0].get("day", {})
    return {
        "city": str((d.get("location") or {}).get("name", city)).upper(),
        "temp_f": _i(cur.get("temp_f")), "feels_like_f": _i(cur.get("feelslike_f")),
        "hi_f": _i(day.get("maxtemp_f")), "lo_f": _i(day.get("mintemp_f")),
        "desc": str((cur.get("condition") or {}).get("text", "CURRENT CONDITIONS")).upper(),
        "code": None, "humidity": _i(cur.get("humidity")),
        "wind_mph": cur.get("wind_mph"), "cloud_cover": _i(cur.get("cloud")),
    }


def _qweather(client, lat, lon, city, key):
    loc = f"{lon:.2f},{lat:.2f}"
    headers = {"Authorization": f"Bearer {key}"}
    now = client.get("https://devapi.qweather.com/v7/weather/now",
                     params={"location": loc, "lang": "en", "unit": "i"},
                     headers=headers).json().get("now", {})
    day = (client.get("https://devapi.qweather.com/v7/weather/3d",
                      params={"location": loc, "lang": "en", "unit": "i"},
                      headers=headers).json().get("daily") or [{}])[0]
    return {
        "city": city, "temp_f": _i(now.get("temp")),
        "feels_like_f": _i(now.get("feelsLike")),
        "hi_f": _i(day.get("tempMax")), "lo_f": _i(day.get("tempMin")),
        "desc": str(now.get("text", "CURRENT CONDITIONS")).upper(), "code": None,
        "humidity": _i(now.get("humidity")), "wind_mph": now.get("windSpeed"),
        "cloud_cover": _i(now.get("cloud")),
    }


_PROVIDERS = {
    "openmeteo": _openmeteo, "openweather": _openweather,
    "weatherapi": _weatherapi, "qweather": _qweather,
}


def fetch_current(settings) -> dict:
    """Current conditions for the global location via the global provider. Falls
    back to keyless Open-Meteo when a keyed provider is missing its key OR fails /
    returns an error body (bad key, rate-limited, outage). Returns
    ``{ok: False, error, provider}`` only if Open-Meteo itself fails; never raises."""
    provider = str(settings.get("weather_provider", "openmeteo") or "openmeteo").lower()
    key = str(settings.get("weather_api_key", "") or "").strip()
    if provider not in _PROVIDERS or (provider != "openmeteo" and not key):
        provider = "openmeteo"          # keyless default — weather works with no key
    lat, lon, city = _resolve_location(settings)
    cache_key = (provider, key, round(lat, 3), round(lon, 3))
    hit = _cache.get(cache_key)
    if hit and (time.time() - hit[0]) < _CACHE_TTL:
        return hit[1]
    try:
        with _Client(timeout=8.0) as client:
            data = None
            if provider != "openmeteo":
                try:
                    got = _PROVIDERS[provider](client, lat, lon, city, key)
                    # A keyed provider that 401s/429s still returns 200-ish JSON
                    # with no temperature: treat a missing temp as a failure.
                    if got.get("temp_f") is not None:
                        data = got
                    else:
                        log.warning("weather provider %s returned no data; using open-meteo", provider)
                except Exception as e:  # noqa: BLE001
                    log.warning("weather provider %s failed (%s); using open-meteo", provider, e)
                if data is None:
                    provider = "openmeteo"
            if data is None:
                data = _openmeteo(client, lat, lon, city, key)
        data.update(ok=True, provider=provider, lat=lat, lon=lon)
        _cache[cache_key] = (time.time(), data)   # cache only successful fetches
        return data
    except Exception as e:  # noqa: BLE001
        log.warning("weather fetch failed: %s", e)
        return {"ok": False, "error": str(e), "provider": provider}
