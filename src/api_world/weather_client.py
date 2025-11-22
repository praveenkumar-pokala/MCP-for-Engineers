"""Weather client using a real, free API (Open-Meteo).

This module focuses on *classic API-style* usage:
- You must know the endpoint
- You must know the required query parameters
- You must understand the JSON structure of the response
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, List

import requests


BASE_URL = "https://api.open-meteo.com/v1/forecast"


@dataclass
class CityConfig:
    name: str
    latitude: float
    longitude: float


# Minimal city registry just for demonstration.
CITY_REGISTRY: Dict[str, CityConfig] = {
    "hyderabad": CityConfig("Hyderabad", 17.38, 78.49),
    "london": CityConfig("London", 51.5072, -0.1276),
    "new york": CityConfig("New York", 40.7128, -74.0060),
}


class WeatherAPIError(RuntimeError):
    """Raised when the weather API call fails."""


def get_city_config(city: str) -> CityConfig:
    key = city.strip().lower()
    if key not in CITY_REGISTRY:
        raise ValueError(
            f"Unsupported city '{city}'. Supported: {', '.join(sorted(CITY_REGISTRY.keys()))}"
        )
    return CITY_REGISTRY[key]


def fetch_daily_weather(city: str, days: int = 3) -> Dict[str, Any]:
    """Fetch daily weather for the given city using Open-Meteo.

    For teaching purposes, we request a very small set of fields:
    - daily temperature max
    - daily temperature min
    - daily precipitation probability

    Documentation: https://open-meteo.com/en/docs
    """
    cfg = get_city_config(city)
    params = {
        "latitude": cfg.latitude,
        "longitude": cfg.longitude,
        "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max"],
        "timezone": "auto",
    }

    try:
        resp = requests.get(BASE_URL, params=params, timeout=10)
        resp.raise_for_status()
    except Exception as exc:  # noqa: BLE001
        raise WeatherAPIError(f"Weather API request failed: {exc}") from exc

    data = resp.json()
    # For simplicity, we let the caller slice the required number of days.
    return data


def summarize_daily_weather(city: str, days: int = 3) -> str:
    """Summarize the next few days of weather for teaching/demo purposes."""
    data = fetch_daily_weather(city, days=days)
    daily = data.get("daily", {})
    dates: List[str] = daily.get("time", [])
    tmax: List[float] = daily.get("temperature_2m_max", [])
    tmin: List[float] = daily.get("temperature_2m_min", [])
    prcp_prob: List[float] = daily.get("precipitation_probability_max", [])

    lines = [f"Weather outlook for {city.title()}:"]
    for i in range(min(days, len(dates))):
        date = dates[i]
        hi = tmax[i] if i < len(tmax) else "?"
        lo = tmin[i] if i < len(tmin) else "?"
        rain = prcp_prob[i] if i < len(prcp_prob) else "?"
        lines.append(
            f"- {date}: high {hi}°C, low {lo}°C, rain probability {rain}%"
        )

    return "\n".join(lines)
