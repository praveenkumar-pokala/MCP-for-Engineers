"""MCP server exposing trip-planning capabilities as *tools*.

This module uses the official MCP Python SDK (FastMCP helper) to define tools that:
- wrap the same external APIs used in api_world
- present them as *high-level capabilities* for an LLM/agent.

Key design idea:

> In the API world, you orchestrate everything manually in your code.
> In the MCP world, you define *tools*, and the model can decide when/how to use them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal, Dict, Any

from mcp.server.fastmcp import FastMCP

from ..api_world.weather_client import summarize_daily_weather
from ..api_world.currency_client import convert_currency
from ..api_world.planner_api_style import pick_budget_profile, TravelerType


mcp = FastMCP("TripPlannerMCP", json_response=True)


@dataclass
class TripSummary:
    origin_city: str
    dest_city: str
    traveler_type: TravelerType
    home_currency: str
    days_of_weather: int
    weather_summary: str
    dest_daily_cost: float
    dest_currency: str
    fx_rate: float
    converted_daily_cost: float


@mcp.tool()
def get_weather(city: str, days: int = 3) -> str:
    """Get a human-readable, short-term weather outlook for a city."""
    return summarize_daily_weather(city, days=days)


@mcp.tool()
def estimate_daily_budget(
    city: str,
    traveler_type: Literal["budget", "standard", "premium"] = "standard",
    home_currency: str = "INR",
) -> Dict[str, Any]:
    """Estimate daily budget in both destination and home currency.

    Returns a JSON dict containing:
    - dest_city
    - traveler_type
    - dest_daily_cost
    - dest_currency
    - home_currency
    - fx_rate
    - home_daily_cost
    """
    profile = pick_budget_profile(city, traveler_type)
    fx_result = convert_currency(
        amount=profile.base_daily_cost,
        from_currency=profile.currency,
        to_currency=home_currency,
    )
    return {
        "dest_city": city.title(),
        "traveler_type": traveler_type,
        "dest_daily_cost": profile.base_daily_cost,
        "dest_currency": profile.currency,
        "home_currency": home_currency.upper(),
        "fx_rate": fx_result.rate,
        "home_daily_cost": fx_result.converted_amount,
    }


@mcp.tool()
def plan_trip_summary(
    origin_city: str,
    dest_city: str,
    traveler_type: Literal["budget", "standard", "premium"] = "standard",
    home_currency: str = "INR",
    days_of_weather: int = 3,
) -> Dict[str, Any]:
    """High-level trip planner tool that composes weather + budget.

    This is the type of tool an LLM *loves*:
    - it encapsulates a multi-step workflow
    - it exposes a small, clean parameter surface
    - it lets the model answer complex user queries in one call
    """
    weather_summary = summarize_daily_weather(dest_city, days=days_of_weather)
    profile = pick_budget_profile(dest_city, traveler_type)
    fx_result = convert_currency(
        amount=profile.base_daily_cost,
        from_currency=profile.currency,
        to_currency=home_currency,
    )

    summary = TripSummary(
        origin_city=origin_city.title(),
        dest_city=dest_city.title(),
        traveler_type=traveler_type,
        home_currency=home_currency.upper(),
        days_of_weather=days_of_weather,
        weather_summary=weather_summary,
        dest_daily_cost=profile.base_daily_cost,
        dest_currency=profile.currency,
        fx_rate=fx_result.rate,
        converted_daily_cost=fx_result.converted_amount,
    )
    return asdict(summary)


def main() -> None:
    """Entry point for starting the MCP server.

    In a real deployment, this would be invoked by an MCP-compatible client
    (e.g., ChatGPT, Claude Desktop, or a custom agent runner) which speaks
    the MCP protocol over stdio or sockets.

    Here, we just call `run()` to make it available.
    """
    # This will start the FastMCP event loop and serve tools over stdio.
    mcp.run()


if __name__ == "__main__":
    main()
