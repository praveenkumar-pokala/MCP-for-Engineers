"""Trip planner that manually orchestrates multiple APIs (API world).

This script shows the *classic way* of answering a question like:

    "I'm travelling from Hyderabad to London.
     What is the weather like and what rough daily budget in INR should I plan?"


Key pain points highlighted:

- You must manually:
  - choose which APIs to call (weather + FX)
  - know their endpoints and parameters
  - parse their JSON
  - glue everything into a human-readable reply
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .weather_client import summarize_daily_weather
from .currency_client import convert_currency


TravelerType = Literal["budget", "standard", "premium"]


@dataclass
class BudgetProfile:
    """Simplified daily budget profile in destination currency."""
    traveler_type: TravelerType
    base_daily_cost: float  # in destination currency
    currency: str


BUDGET_TABLE = {
    # For London, GBP amounts (very rough numbers for demo).
    "london": {
        "budget": BudgetProfile("budget", 60.0, "GBP"),
        "standard": BudgetProfile("standard", 100.0, "GBP"),
        "premium": BudgetProfile("premium", 200.0, "GBP"),
    }
}


def pick_budget_profile(city: str, traveler_type: TravelerType) -> BudgetProfile:
    city_key = city.strip().lower()
    if city_key not in BUDGET_TABLE:
        raise ValueError(
            f"No budget profile configured for '{city}'. "
            f"Configured cities: {', '.join(BUDGET_TABLE.keys())}"
        )
    city_profiles = BUDGET_TABLE[city_key]
    if traveler_type not in city_profiles:
        raise ValueError(
            f"No budget profile for traveler type '{traveler_type}' in city '{city}'. "
            f"Supported types: {', '.join(city_profiles.keys())}"
        )
    return city_profiles[traveler_type]


def plan_trip_api_style(
    origin_city: str,
    dest_city: str,
    traveler_type: TravelerType = "standard",
    home_currency: str = "INR",
    days_of_weather: int = 3,
) -> str:
    """End-to-end planner using *only* raw API-style clients.

    This function:
    - Gets a simple weather forecast for the destination.
    - Picks a destination-currency daily budget based on traveler type.
    - Converts that budget into the home currency (INR by default).
    - Returns a formatted, human-readable summary.
    """
    # 1. Weather summary (manual orchestration)
    weather_summary = summarize_daily_weather(dest_city, days=days_of_weather)

    # 2. Budget in destination currency
    profile = pick_budget_profile(dest_city, traveler_type)
    fx_result = convert_currency(
        amount=profile.base_daily_cost,
        from_currency=profile.currency,
        to_currency=home_currency,
    )

    lines = [
        f"Trip plan from {origin_city.title()} to {dest_city.title()} ({traveler_type} traveler):",
        "",
        "Weather outlook:",
        weather_summary,
        "",
        "Budget estimation:",
        f"- Base daily cost in {dest_city.title()}: {profile.base_daily_cost:.0f} {profile.currency}",
        f"- FX rate {profile.currency} -> {home_currency}: {fx_result.rate:.2f}",
        f"- Approx. daily budget in {home_currency}: {fx_result.converted_amount:.0f} {home_currency}",
    ]

    return "\n".join(lines)


def main() -> None:
    # Hard-coded scenario for demo purposes.
    origin = "Hyderabad"
    dest = "London"
    traveler_type: TravelerType = "standard"
    print("[API WORLD] Manual orchestration demo\n" + "-" * 40)
    result = plan_trip_api_style(origin, dest, traveler_type)
    print(result)


if __name__ == "__main__":
    main()
