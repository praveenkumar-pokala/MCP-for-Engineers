"""Minimal MCP server exposing echo + weather tools.

Tools:
  - echo(message): echoes text back
  - get_weather(city): fetches real current weather using Open-Meteo

Run:
    python weather_server.py
"""

from __future__ import annotations

import requests
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WeatherDemo")

# Simple mapping of demo cities to coordinates
CITY_COORDS = {
    "Hyderabad": (17.38, 78.49),
    "London": (51.5072, -0.1276),
    "Bangalore": (12.9716, 77.5946),
    "New York": (40.7128, -74.0060),
}

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


@mcp.tool()
async def echo(message: str) -> str:
    """Echo the message back, prefixed by MCP."""
    return f"[MCP echo] {message}"


@mcp.tool()
async def get_weather(city: str) -> str:
    """Get a simple current-weather summary for a supported city.

    Uses the free Open-Meteo API (no key required).
    If the city is not in the demo list, a default coordinate is used.
    """
    name = city.strip() or "Hyderabad"
    lat, lon = CITY_COORDS.get(name, CITY_COORDS["Hyderabad"])

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
    }
    try:
        resp = requests.get(OPEN_METEO_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        cw = data.get("current_weather", {})
        temp = cw.get("temperature")
        wind = cw.get("windspeed")
        time = cw.get("time")
        return (
            f"Current weather in {name}: {temp}°C, wind {wind} km/h "
"
            f"(time: {time})."
"
        )
    except Exception as e:  # noqa: BLE001
        return f"Could not fetch weather for {name}: {e}"


if __name__ == "__main__":
    # Expose tools via stdio (for local MCP clients)
    mcp.run(transport="stdio")
