"""MCP client + OpenAI demo.

This script:
  1. Starts `weather_server.py` as an MCP server over stdio.
  2. Uses the MCP Python SDK to connect and discover tools.
  3. Uses OpenAI Chat Completions with `tools=` so the model can:
       - decide when to call MCP tools
       - use the results in its final answer.

Run:
    export OPENAI_API_KEY="sk-..."   # set your key
    python mcp_client_openai.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from contextlib import AsyncExitStack
from typing import Any, Awaitable, Callable, ClassVar, Self

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI


MODEL = "gpt-4o-mini"  # any tool-capable model is fine


# ---------------------------------
# 1. MCP client (connects to server)
# ---------------------------------
class MCPClient:
    """Wrapper that launches and connects to the MCP server."""

    client_session: ClassVar[ClientSession]

    def __init__(self, server_path: str):
        self.server_path = server_path
        self.exit_stack = AsyncExitStack()

    async def __aenter__(self) -> Self:
        type(self).client_session = await self._connect_to_server()
        return self

    async def __aexit__(self, *exc_info) -> None:
        await self.exit_stack.aclose()

    async def _connect_to_server(self) -> ClientSession:
        """Start the MCP server process and create a ClientSession."""
        try:
            read, write = await self.exit_stack.enter_async_context(
                stdio_client(
                    server=StdioServerParameters(
                        command="sh",
                        args=["-c", f"{sys.executable} {self.server_path} 2>/dev/null"],
                        env=None,
                    )
                )
            )
            client_session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await client_session.initialize()
            return client_session
        except Exception as e:  # noqa: BLE001
            raise RuntimeError(f"Failed to connect to MCP server: {e}") from e

    async def list_all_members(self) -> None:
        """Print tools/prompts/resources for teaching purposes."""
        print("MCP Server Members")
"
        print("=" * 50)
"
        sections: dict[str, Callable[[], Awaitable[Any]]] = {
"
            "tools": self.client_session.list_tools,
"
            "prompts": self.client_session.list_prompts,
"
            "resources": self.client_session.list_resources,
"
        }
"
        for section, listing_method in sections.items():
"
            try:
"
                response = await listing_method()
"
                items = getattr(response, section)
"
                if items:
"
                    print(f"\n{section.upper()} ({len(items)}):")
"
                    print("-" * 30)
"
                    for item in items:
"
                        desc = item.description or "No description"
"
                        print(f"  > {item.name} - {desc}")
"
                else:
"
                    print(f"\n{section.upper()}: None")
"
            except Exception as e:  # noqa: BLE001
"
                print(f"\n{section.upper()}: Error - {e}")
"
        print("\n" + "=" * 50)
"


# ---------------------------------
# 2. OpenAI + MCP glue
# ---------------------------------
class OpenAIQueryHandler:
    """Bridge between OpenAI tool-calling and MCP tools."""

    def __init__(self, client_session: ClientSession):
        self.client_session = client_session
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Set OPENAI_API_KEY environment variable first.")
        self.openai = OpenAI(api_key=api_key)

    async def process_query(self, query: str) -> str:
        """Handle one user query end-to-end."""
        messages: list[dict[str, Any]] = [
            {"role": "user", "content": query},
        ]

        # 1) Ask the model, giving it the MCP tools as OpenAI tools
        initial = self.openai.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=await self._tools_for_openai(),
            max_tokens=400,
        )

        current = initial.choices[0].message
        fragments: list[str] = []

        if current.content:
            fragments.append(current.content)

        tool_calls = current.tool_calls or []

        if tool_calls:
            # Add the assistant tool-call message to the conversation
            messages.append(
                {
                    "role": "assistant",
"
                    "content": current.content or "",
"
                    "tool_calls": [tc.to_dict() for tc in tool_calls],
"
                }
"
            )
"

            # 2) Execute each requested tool via MCP
            for tc in tool_calls:
"
                tool_result = await self._execute_mcp_tool(tc)
"
                fragments.append(tool_result["log"])
"
                messages.append(tool_result["message"])
"

            # 3) Ask the model again, now with tool results included
            final = self.openai.chat.completions.create(
                model=MODEL,
                messages=messages,
                max_tokens=400,
            )
            final_msg = final.choices[0].message
            if final_msg.content:
                fragments.append(final_msg.content)

        return "\n".join(fragments) or "(no response)"

    async def _tools_for_openai(self) -> list[dict[str, Any]]:
        """Convert MCP tools → OpenAI tools schema."""
        resp = await self.client_session.list_tools()
        tools: list[dict[str, Any]] = []
        for tool in resp.tools:
            schema = getattr(tool, "inputSchema", {"type": "object", "properties": {}})
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "No description",
                        "parameters": schema,
                    },
                }
            )
        return tools

    async def _execute_mcp_tool(self, tool_call) -> dict[str, Any]:
        """Call the MCP tool requested by the model."""
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments or "{}")

        try:
            result = await self.client_session.call_tool(name, args)
            content = result.content[0].text if result.content else ""
            log = f"[Used {name}({args})]"
        except Exception as e:  # noqa: BLE001
            content = f"Error calling tool {name}: {e}"
            log = content

        return {
            "log": log,
            "message": {
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": content,
            },
        }


# ---------------------------------
# 3. Interactive demo loop
# ---------------------------------
async def main() -> None:
    server_path = "./weather_server.py"

    async with MCPClient(server_path) as client:
        print("✅ Connected to MCP server\n")
        await client.list_all_members()

        handler = OpenAIQueryHandler(client.client_session)

        print("MCP + OpenAI Chat Demo")
"
        print("Ask things like:")
"
        print("  - What is the weather in London?")
"
        print("  - Can you echo back this message via MCP?")
"
        print("Type 'quit' to exit.\n")
"

        while True:
"
            user = input("You: ").strip()
"
            if not user:
"
                continue
"
            if user.lower() in {"quit", "exit"}:
"
                break
"

            answer = await handler.process_query(user)
"
            print("\nAssistant:\n" + answer + "\n")
"


if __name__ == "__main__":
    asyncio.run(main())
