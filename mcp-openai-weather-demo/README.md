# MCP + OpenAI Weather Demo 🌦️🤖

This repo shows, with **real code**, how:

- an **MCP server** exposes tools, and  
- an **MCP client + OpenAI** let a model *discover and call* those tools.

It is designed to be:
- Small enough to read in one sitting
- Powerful enough to teach *how LLMs actually use MCP tools*


## 🔧 What this demo does

We implement:

1. An **MCP server** (`weather_server.py`) that exposes two tools:
   - `echo(message: str)` → echoes text back
   - `get_weather(city: str)` → uses **Open-Meteo** (free, no API key) to fetch current weather for a few demo cities

2. An **MCP client** (`mcp_client_openai.py`) that:
   - Launches the MCP server over stdio
   - Uses the MCP Python SDK to:
     - initialize a `ClientSession`
     - list tools
     - call tools
   - Uses **OpenAI Chat Completions** with `tools=` so the model can:
     - see the MCP tools as functions
     - decide if it should call them
     - integrate their results into a natural-language answer


## 🧠 The mental model

**MCP server** (tools provider):

- Knows nothing about OpenAI or chat.
- Just exposes capabilities (e.g., `get_weather(city)`).

**MCP client** (bridge):

- Connects to the MCP server (via stdio).
- Calls `list_tools()` to discover tools.
- Converts each MCP tool → OpenAI tool schema (`type="function"`).
- Calls MCP tools when the model asks for them.
- Feeds tool outputs back into the model.

**OpenAI model**:

- Sees a list of tools with names, descriptions, and JSON schemas.
- Decides *which* tool to call and *with what parameters*.
- Never deals with MCP protocol details; that’s the client’s job.


## 📦 Files

```text
mcp-openai-weather-demo/
├── README.md
├── requirements.txt
├── weather_server.py         # MCP server with echo + get_weather tools
└── mcp_client_openai.py      # MCP client + OpenAI tool-calling bridge
```


## 🚀 Getting started

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="sk-..."   # on Windows: set OPENAI_API_KEY=sk-...
```


### 2. Run the demo

```bash
python mcp_client_openai.py
```

You should see something like:

```text
✅ Connected to MCP server

MCP Server Members
==================================================
TOOLS (2):
  > echo - Echo the message back, prefixed by MCP.
  > get_weather - Get a simple current-weather summary for a city.
...
MCP + OpenAI Chat Demo
Ask things like:
  - What is the weather in London?
  - Can you echo back this message via MCP?
Type 'quit' to exit.
```


### 3. Try some queries

Examples:

```text
You: What is the weather in London today?

Assistant:
[Used get_weather({'city': 'London'})]
It looks like it's roughly 18°C in London right now with some wind.
...

You: Can you echo back this text but via MCP tools?

Assistant:
[Used echo({'message': 'echo back this text but via MCP tools'})]
[MCP echo] echo back this text but via MCP tools
Sure! I echoed your message using the MCP echo tool, as shown above.
```


## 🧩 How this explains MCP client vs MCP server

### MCP server (`weather_server.py`)

- Defines **what is possible**:
  - `echo(message)`
  - `get_weather(city)`
- Talks MCP over stdio (`mcp.run(transport="stdio")`).
- Has no idea about prompts, chat windows, or OpenAI.

### MCP client (`mcp_client_openai.py`)

- Knows:
  - how to **launch** the server as a subprocess
  - how to create a `ClientSession` to talk MCP
  - how to **list tools** and **call tools**
  - how to present those tools to OpenAI via the `tools=` parameter

- When the model returns a `tool_call`, the client:
  - Reads `tool_call.function.name` and `.arguments`
  - Calls `client_session.call_tool(name, args)`
  - Feeds the result back into the model as a `role="tool"` message


### The key insight

> The LLM does *not* “speak MCP protocol.”
>
> The **MCP client** speaks MCP.
>
> The LLM only sees **tool schemas** and chooses which tool to call.
>
> The client takes those decisions and executes the real MCP protocol.


## 🧪 Teaching usage

This repo is great for:

- Workshops on **Agentic AI**
- Explaining **APIs vs MCP tools**
- Showing how **tool-calling** works with a real backend
- Interviews / tech talks on LLM systems design

You can extend it by:

- Adding more tools (e.g., `get_forecast_range`, `compare_cities`)
- Using more realistic data sources (databases, RAG, internal APIs)
- Turning the client into a LangGraph / agent framework node

Happy hacking! 🌦️🤖
