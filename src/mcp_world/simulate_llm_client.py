"""Simulated 'LLM client' for the TripPlannerMCP server.

This module is **not** a full MCP client implementation. Instead, it:

- Imports the same FastMCP server instance.
- Introspects the tools (as a proxy for what a real MCP client would see).
- Calls the high-level `plan_trip_summary` tool directly in Python.

The goal is to demonstrate *conceptually* what an LLM-driven flow would look like:

    User: "I'm going from Hyderabad to London. What should I expect?"
    LLM:  (decides to call plan_trip_summary with appropriate arguments)
    MCP:  (executes weather + budget logic and returns structured JSON)
    LLM:  (turns JSON into a narrative answer for the user)
"""

from __future__ import annotations

import json
import textwrap

from .mcp_server import mcp, plan_trip_summary


def demo_introspect_tools() -> None:
    """Print out available tools as a teaching aid."""
    tools = mcp._server_state.tools  # internal; fine for demo / teaching
    print("[MCP WORLD] Tools advertised by TripPlannerMCP")
    print("-" * 60)
    for name, tool in tools.items():
        print(f"Tool: {name}")
        if tool.description:
            print(f"  Description: {tool.description}")
        print("  Parameters schema:")
        print(textwrap.indent(json.dumps(tool.parameters, indent=2), "    "))
        print()


def demo_simulated_llm_call() -> None:
    """Simulate what an LLM might do in natural language terms."""
    # In a real MCP setting, the model would:
    # - parse the user's natural-language request
    # - map it to a tool + arguments
    # Here, we hard-code that mapping for clarity.
    origin = "Hyderabad"
    dest = "London"
    traveler_type = "standard"

    print("[MCP WORLD] Simulated LLM decision:")
    print(
        f'  → Call tool plan_trip_summary(origin_city="{origin}", '
        f'dest_city="{dest}", traveler_type="{traveler_type}")'
    )
    result = plan_trip_summary(
        origin_city=origin,
        dest_city=dest,
        traveler_type=traveler_type,  # type: ignore[arg-type]
        home_currency="INR",
        days_of_weather=3,
    )

    print()
    print("[MCP WORLD] Raw tool JSON result (what the model sees):")
    print(json.dumps(result, indent=2))

    # The final step would be the model turning this into a nice narrative.
    print()
    print("[MCP WORLD] Example final answer the LLM could generate:")
    print(
        textwrap.dedent(
            f"""            For your trip from {result['origin_city']} to {result['dest_city']} as a {result['traveler_type']} traveler:

            Weather outlook (next {result['days_of_weather']} days):
            {result['weather_summary']}

            Budget estimation:
            - Base daily cost in {result['dest_city']}: {result['dest_daily_cost']:.0f} {result['dest_currency']}
            - Approx. daily budget in {result['home_currency']}: {result['converted_daily_cost']:.0f} {result['home_currency']}

            You can adjust the traveler type (budget / standard / premium) to explore different budget levels.
            """
        ).strip()
    )


def main() -> None:
    demo_introspect_tools()
    print()
    demo_simulated_llm_call()


if __name__ == "__main__":
    main()
