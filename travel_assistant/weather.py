"""Weather lookup using the keyless Open-Meteo forecast endpoint."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
MAX_FORECAST_DAYS = 16

# Approximate city-center coordinates for the cities in the supplied datasets.
CITY_COORDINATES = {
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Delhi": (28.6139, 77.2090),
    "Goa": (15.2993, 74.1240),
    "Hyderabad": (17.3850, 78.4867),
    "Jaipur": (26.9124, 75.7873),
    "Kolkata": (22.5726, 88.3639),
    "Mumbai": (19.0760, 72.8777),
}

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Light rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Freezing rain",
    67: "Heavy freezing rain",
    71: "Light snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Light rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Light snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with light hail",
    99: "Thunderstorm with heavy hail",
}


def get_weather_forecast(
    city: str,
    start_date: date,
    trip_days: int,
    today: date | None = None,
) -> dict[str, Any]:
    """Return available daily forecasts and explain dates outside the API horizon."""
    today = today or date.today()
    coordinates = next(
        (coords for name, coords in CITY_COORDINATES.items() if name.casefold() == city.casefold()),
        None,
    )
    if coordinates is None:
        return {
            "status": "unavailable",
            "message": f"No coordinates are configured for {city}.",
            "days": [],
        }
    if start_date < today:
        return {
            "status": "unavailable",
            "message": "The requested trip date is in the past; no live forecast is available.",
            "days": [],
        }
    if (start_date - today).days >= MAX_FORECAST_DAYS:
        return {
            "status": "unavailable",
            "message": f"Open-Meteo provides forecasts up to {MAX_FORECAST_DAYS} days ahead. Weather will be shown when dates enter that window.",
            "days": [],
        }

    latitude, longitude = coordinates
    try:
        response = requests.get(
            OPEN_METEO_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max",
                "forecast_days": MAX_FORECAST_DAYS,
                "timezone": "auto",
            },
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        daily = payload.get("daily", {}) if isinstance(payload, dict) else {}
        forecast_dates = daily.get("time", []) if isinstance(daily, dict) else []
        if not isinstance(forecast_dates, list):
            forecast_dates = []
        forecasts: dict[str, dict[str, Any]] = {}
        end_date_exclusive = start_date + timedelta(days=trip_days)
        for index, forecast_date in enumerate(forecast_dates):
            if not isinstance(forecast_date, str):
                continue
            if forecast_date < start_date.isoformat() or forecast_date >= end_date_exclusive.isoformat():
                continue
            code = _at(daily.get("weather_code", []), index)
            try:
                condition = (
                    WEATHER_CODES.get(int(code), "Conditions unavailable")
                    if code is not None
                    else "Conditions unavailable"
                )
            except (TypeError, ValueError, OverflowError):
                condition = "Conditions unavailable"
            forecasts[forecast_date] = {
                "date": forecast_date,
                "condition": condition,
                "temperature_max_c": _at(daily.get("temperature_2m_max", []), index),
                "temperature_min_c": _at(daily.get("temperature_2m_min", []), index),
                "precipitation_probability_max": _at(daily.get("precipitation_probability_max", []), index),
            }
        if forecasts:
            expected = min(trip_days, (today + timedelta(days=MAX_FORECAST_DAYS - 1) - start_date).days + 1)
            has_full_trip = expected >= trip_days and len(forecasts) >= trip_days
            status = "ok" if has_full_trip else "partial"
            message = (
                "Forecast available for every trip day."
                if status == "ok"
                else "Only part of the trip falls within the current forecast window."
            )
            return {"status": status, "message": message, "days": list(forecasts.values())}
        return {
            "status": "unavailable",
            "message": "No forecast data was returned for the requested dates.",
            "days": [],
        }
    except (requests.RequestException, ValueError, TypeError) as exc:
        return {
            "status": "unavailable",
            "message": f"Weather service is unavailable: {exc}",
            "days": [],
        }


def _at(values: list[Any], index: int) -> Any:
    return values[index] if isinstance(values, list) and 0 <= index < len(values) else None

