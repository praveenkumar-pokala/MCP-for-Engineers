# Complex Trip Planner: API vs MCP Demo 🌍✈️

This repository demonstrates the **difference between classic APIs and MCP-style tools** using a more complex, but still intuitive, example:

> **Trip Cost & Weather Planner**  
> “I’m travelling from Hyderabad to London.  
> What’s the expected weather, and what rough daily budget in INR should I plan for?”

We implement this scenario in **two worlds**:

1. `api_world/` – The *old way*: you manually orchestrate multiple REST APIs.
2. `mcp_world/` – The *new way*: the same capabilities are wrapped as **MCP tools**, so an LLM (or agent) can discover and call them.

---

## 🧠 Intuition Behind the Example

To answer a seemingly simple user request, we actually need to:

1. **Understand locations**  
   - Map city names to coordinates (for weather)
   - Know which country a city belongs to
2. **Get weather forecast**  
   - Call a real, free weather API (Open-Meteo)
3. **Estimate daily budget**  
   - Assume a base daily cost in the **destination currency**
   - Convert it to INR using a real, free FX API (exchangerate.host)

### What makes this *complex*:

- We need **multiple external systems**:
  - Weather API
  - FX conversion API
- We need **chained reasoning**:
  - city → coordinates → weather
  - city → country → currency → FX rate → INR budget
- We want to expose this in a way that an **LLM can use autonomously**, not just a human developer.

---

## 🧱 Repo Structure

```text
complex-api-vs-mcp-trip-planner/
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── api_world/
│   │   ├── __init__.py
│   │   ├── weather_client.py
│   │   ├── currency_client.py
│   │   └── planner_api_style.py
│   └── mcp_world/
│       ├── __init__.py
│       ├── mcp_server.py
│       └── simulate_llm_client.py
└── notebooks/
    └── trip_planner_api_vs_mcp_demo.ipynb
```

---

## 🌐 Part 1 – API World (Manual Orchestration)

The `api_world` module shows how **you**, the developer, must:

- Know the endpoints and query parameters
- Know the JSON structure of each response
- Decide in what order to call which API
- Manually glue all the data together into a final reply

We use **real, free endpoints**:

- **Weather:** [Open-Meteo](https://open-meteo.com/en/docs) – no API key required  
  - Used to get 7-day forecast for a city (via pre-mapped lat/lon)
- **FX conversion:** [exchangerate.host](https://exchangerate.host/#/#docs) – free, no key  
  - Used to convert a base daily budget from destination currency → INR

> In API world, your code is sprawling across multiple clients and JSON payloads.  
> The **model knows nothing** about these abilities unless you explicitly prompt it and glue it all together.

---

## 🤖 Part 2 – MCP World (Tool-Based Orchestration)

The `mcp_world` module exposes the same capabilities as **MCP tools**, using the official Python SDK (`mcp.server.fastmcp.FastMCP`).

It defines tools like:

- `get_weather(city: str)`  
  → returns a concise weather summary for the next few days for that city.
- `estimate_daily_budget(city: str, traveler_type: str = "standard")`  
  → picks a base cost in the city’s currency (e.g., GBP for London), then converts to INR.
- `plan_trip_summary(origin_city: str, dest_city: str, traveler_type: str = "standard")`  
  → high-level orchestration tool that **internally composes** the other tools.

### Key differences vs plain API:

- The MCP server **self-describes** available tools:
  - Tool names
  - Parameter schemas
  - Human-readable descriptions
- An MCP-aware client (like ChatGPT, Claude Desktop, or your own agent) can:
  - Discover tools dynamically
  - Choose when to call them
  - Chain them into multi-step workflows

> **APIs let humans talk to machines.  
> MCP lets machines talk to machines.**

---

## 🚀 How To Run

### 1️⃣ Set up the environment

```bash
git clone <this-repo-url>
cd complex-api-vs-mcp-trip-planner

python -m venv .venv
source .venv/bin/activate  # on Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

If you run this in **Google Colab**, just upload the folder or mount it from Drive and use:

```python
!pip install -r requirements.txt
```

---

### 2️⃣ Run the API-world demo

```bash
python -m src.api_world.planner_api_style
```

This will:

- Fetch real weather data via Open-Meteo
- Fetch a real FX rate via exchangerate.host
- Print a combined summary like:

> For your trip from Hyderabad to London:  
> - Expected temperatures in London for the next few days are around …  
> - A rough daily budget for a standard traveler is about X,XXX INR per day.

All orchestration is **manual**.

---

### 3️⃣ Run the MCP server

```bash
python -m src.mcp_world.mcp_server
```

This starts an MCP server exposing:

- `get_weather`
- `estimate_daily_budget`
- `plan_trip_summary`

You can:

- Connect to this server with any MCP-compatible client, **or**
- Run the included simulated client:

```bash
python -m src.mcp_world.simulate_llm_client
```

The simulated client behaves like a dumb LLM that:

1. “Discovers” tools from the server
2. Calls `plan_trip_summary` with parameters derived from a natural-language style configuration
3. Prints the final structured response

---

## 🧪 Notebook Demo

The `notebooks/trip_planner_api_vs_mcp_demo.ipynb` notebook is designed for **teaching**:

- First half:  
  – Shows raw API calls  
  – Visualizes response JSON  
  – Walks through manual orchestration

- Second half:  
  – Shows MCP tool definitions  
  – Introspects tool metadata  
  – Demonstrates a simulated agent calling higher-level tools

You can open it directly in **Google Colab** by uploading the repo or using a GitHub link.

---

## 🎯 Teaching Angles

This repo is perfect for explaining:

1. **Why APIs are low-level plumbing**  
   - You think in terms of endpoints and payloads.
2. **Why MCP tools are high-level capabilities**  
   - You think in terms of *what the model can do*.
3. **How complex workflows become simpler**  
   - Trip planning mixes weather, FX, assumptions, and user type.
   - In MCP, all of that sits behind a *small set of discoverable tools*.

You can frame it like this:

> *“In the API world, the developer is the orchestrator.  
> In the MCP world, the developer defines tools, and the **model** becomes the orchestrator.”*

---

Happy teaching and hacking! 🌍✈️🤖
