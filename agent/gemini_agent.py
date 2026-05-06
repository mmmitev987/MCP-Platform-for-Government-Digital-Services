"""
agent/gemini_agent.py
────────────────────────────────────────────────────────────────────────────────
Gemini Flash agent that drives the multi-institution MCP gateway.

Architecture
────────────
  ┌─────────────────────────────────────────────────────────────────┐
  │                        User (terminal)                          │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │ natural language
                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                     gemini_agent.py  ◄── YOU ARE HERE           │
  │                                                                 │
  │  1. Spawns gateway/main.py as a subprocess.                    │
  │  2. Connects to it via MCP stdio (one connection).              │
  │  3. Fetches ALL aggregated tools (e.g. uslugi__login,          │
  │     mojtermin__book_appointment …).                             │
  │  4. Converts MCP tool schemas → Gemini FunctionDeclarations.   │
  │  5. Runs the conversation loop:                                 │
  │       User says something →                                     │
  │       Gemini decides which tool(s) to call →                   │
  │       Agent calls them via the MCP gateway →                   │
  │       Gateway routes each call to the right institution →       │
  │       Results are fed back to Gemini →                          │
  │       Gemini produces a final answer for the user.              │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │ MCP JSON-RPC (stdio)
                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    gateway/main.py                              │
  │   Aggregates tools from all institutions under namespaced names │
  └──────────────────┬────────────────────────┬────────────────────┘
       MCP stdio     │                        │   MCP stdio
                     ▼                        ▼
      institutions/uslugi/main.py    institutions/mojtermin/main.py

From this file's perspective, there is only ONE MCP server: the gateway.
The multi-institution routing is completely transparent here.

Security note:
  Gemini sees tool SCHEMAS and tool RESULTS, but never raw cookies,
  session tokens, or credentials.  Login tools open a browser — the user
  types credentials directly there, invisible to this process.

Running:
  python agent/gemini_agent.py
"""

import asyncio
import sys
from pathlib import Path

# ── google-genai SDK (new SDK — NOT google-generativeai) ─────────────────────
from google import genai
from google.genai import types as genai_types

# ── MCP client libraries ──────────────────────────────────────────────────────
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ── Add project root to sys.path ──────────────────────────────────────────────
# This allows importing from institutions/ and shared/ even when the script is
# run directly (python agent/gemini_agent.py) rather than as a module.
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))

# ── Config (only needs the Gemini key — the gateway handles everything else) ──
# We import from a neutral location; institutions/uslugi/config.py also exports
# GEMINI_API_KEY as a convenience.  Pull it directly from env to stay decoupled.
import os
from dotenv import load_dotenv

load_dotenv(PROJECT_ROOT / ".env")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL: str = "gemini-2.5-flash"

if not GEMINI_API_KEY:
    # Fallback to the demo key so the demo still runs out-of-the-box.
    GEMINI_API_KEY = ""

# ── Gemini client ─────────────────────────────────────────────────────────────
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# ── System prompt ──────────────────────────────────────────────────────────────
# This tells Gemini its role, the institutions it can interact with, and the
# security rules it must follow.
SYSTEM_PROMPT = """
You are a helpful assistant for Macedonian citizens interacting with government
online portals.

You have access to MCP tools for TWO institutions:

  1. uslugi.gov.mk  — The main public services portal.
     Tools are prefixed with "uslugi__" (e.g. uslugi__login, uslugi__info_passport_renewal).
     Use these for: passport renewal info, document submissions, administrative procedures.

   2. mojtermin.mk   — The government appointment booking system.
      Tools are prefixed with "mojtermin__" (e.g. mojtermin__get_doctors_by_city,
      mojtermin__get_available_slots, mojtermin__search_resources, mojtermin__get_first_available).
      Use these for: finding doctors, clinics, and locations by name or city;
      searching resources; checking available appointment slots on a specific date,
      across a date range, or finding the first available slot; viewing availability
      summaries; checking all slots in a city on a given date.
      All mojtermin tools are public — no login is required.

SECURITY RULES:
  1. NEVER ask the user for a password or any credentials.
     The uslugi login tool opens a browser — the user types credentials there.
  2. NEVER repeat cookie values, session tokens, or auth headers in your responses.
  3. If a uslugi tool returns a session expired error, tell the user and offer to call uslugi__login.
  4. Keep responses concise and in plain language.
  5. When presenting lists (services, slots, appointments), use bullet points.
  6. If the user asks about something unrelated to these portals, politely explain
     that you are specialised for Macedonian government services.
  7. If the user's request is related to these portals but there is no tool
     available for it, tell the user clearly that this feature is not supported
     yet. Do NOT attempt to improvise or call unrelated tools as a workaround.
     EXCEPTION: for uslugi service lookups, always call uslugi__list_all_services
     before concluding a service is not available — the portal has 994 services
     and search may miss them due to keyword mismatch.
  8. The uslugi.gov.mk search API only understands Macedonian Cyrillic.                                                                                        
     ALWAYS translate the user's query to Macedonian Cyrillic before calling                                                                                   
     uslugi__search_services. For example: "ID card" → "лична карта",                                                                                          
     "passport" → "пасош", "driver license" → "возачка дозвола",                                                                                               
     "construction permit" → "градежна дозвола".
""".strip()


# ═══════════════════════════════════════════════════════════════════════════════
# MCP ↔ Gemini schema conversion helpers
# ═══════════════════════════════════════════════════════════════════════════════

def mcp_tool_to_gemini_function(mcp_tool) -> genai_types.FunctionDeclaration:
    """
    Convert a single MCP Tool definition into a Gemini FunctionDeclaration.

    MCP tools carry a JSON Schema "inputSchema" for their parameters.
    Gemini wants a FunctionDeclaration with a typed parameters schema.
    This function bridges the two formats.

    Args:
        mcp_tool: An MCP types.Tool object (has .name, .description, .inputSchema).

    Returns:
        A genai_types.FunctionDeclaration ready to be passed to Gemini.
    """
    input_schema = mcp_tool.inputSchema or {}
    properties_raw = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    # Convert each JSON Schema property to a Gemini Schema object.
    gemini_properties: dict[str, genai_types.Schema] = {}
    for param_name, param_schema in properties_raw.items():
        # Map JSON Schema type strings to Gemini Type enum values.
        # Unrecognised types fall back to STRING (safe default).
        json_type = param_schema.get("type", "string").upper()
        gemini_type = getattr(genai_types.Type, json_type, genai_types.Type.STRING)

        gemini_properties[param_name] = genai_types.Schema(
            type=gemini_type,
            description=param_schema.get("description", ""),
        )

    parameters = genai_types.Schema(
        type=genai_types.Type.OBJECT,
        properties=gemini_properties,
        required=required,
    )

    return genai_types.FunctionDeclaration(
        name=mcp_tool.name,
        description=mcp_tool.description or "",
        parameters=parameters,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Main agent loop
# ═══════════════════════════════════════════════════════════════════════════════

async def run_agent() -> None:
    """
    Launch the gateway subprocess and run the interactive conversation loop.

    The flow per user message:
      1. Append the user message to conversation history.
      2. Send history + tool definitions to Gemini.
      3. If Gemini returns a function call → execute it via the MCP gateway.
      4. Append the tool result to history.
      5. Repeat steps 2-4 until Gemini produces a plain text answer.
      6. Print the answer and wait for the next user message.
    """

    # ── Launch the gateway as a subprocess ────────────────────────────────────
    # The gateway in turn spawns the institution servers.  From our perspective
    # there is only one subprocess (the gateway), communicating via stdio.
    #
    # We use sys.executable (the current venv Python) so that "import shared"
    # and "import institutions" resolve correctly.
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "gateway.main"],
        cwd=str(PROJECT_ROOT),
    )

    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as mcp_session:

            # ── MCP handshake ──────────────────────────────────────────────────
            # initialize() sends the MCP "initialize" request to the gateway and
            # waits for the response before we can call list_tools / call_tool.
            await mcp_session.initialize()
            print("[Agent] Gateway connected.")

            # ── Fetch aggregated tool list ─────────────────────────────────────
            # The gateway returns all institution tools under namespaced names.
            # e.g. ["uslugi__login", "uslugi__info_passport_renewal",
            #       "mojtermin__login", "mojtermin__get_doctors_by_city", …]
            tools_response = await mcp_session.list_tools()
            mcp_tools = tools_response.tools
            print(f"[Agent] Available tools ({len(mcp_tools)}):")
            for t in mcp_tools:
                print(f"  • {t.name}")

            # ── Convert tool schemas to Gemini format ──────────────────────────
            # Gemini needs all tools in a single Tool object with a list of
            # FunctionDeclarations.  One FunctionDeclaration per MCP tool.
            gemini_tools = [
                genai_types.Tool(
                    function_declarations=[
                        mcp_tool_to_gemini_function(t) for t in mcp_tools
                    ]
                )
            ]

            # ── Conversation history ───────────────────────────────────────────
            # We keep the full turn-by-turn history so Gemini has context across
            # multiple exchanges.  Format: list of genai_types.Content objects.
            history: list[genai_types.Content] = []

            print("\n" + "═" * 65)
            print("  Macedonian Government Services Assistant")
            print("  Institutions: uslugi.gov.mk  |  mojtermin.mk")
            print("  Powered by Gemini Flash  •  Type 'quit' to exit.")
            print("═" * 65 + "\n")

            # ── Interactive conversation loop ──────────────────────────────────
            while True:
                # Read user input from the terminal.
                try:
                    user_input = input("You: ").strip()
                except (KeyboardInterrupt, EOFError):
                    print("\n[Agent] Goodbye.")
                    break

                if user_input.lower() in ("quit", "exit", "q"):
                    print("[Agent] Goodbye.")
                    break

                if not user_input:
                    continue

                # Add the user message to the conversation history.
                history.append(
                    genai_types.Content(
                        role="user",
                        parts=[genai_types.Part(text=user_input)],
                    )
                )

                # ── Agentic inner loop: handle tool calls ──────────────────────
                # Gemini may call multiple tools in sequence before producing
                # a final text answer.  We loop until we get plain text.
                while True:
                    # Send the full conversation history to Gemini.
                    # Gemini has visibility of:
                    #   • The system prompt (role, security rules, institution guide).
                    #   • All prior user messages and assistant responses.
                    #   • All prior tool calls and their results.
                    #   • The current tool schema list.
                    response = gemini_client.models.generate_content(
                        model=GEMINI_MODEL,
                        contents=history,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            tools=gemini_tools,
                            # AUTO lets Gemini choose whether to call a tool
                            # or respond with text on each turn.
                            tool_config=genai_types.ToolConfig(
                                function_calling_config=genai_types.FunctionCallingConfig(
                                    mode="AUTO"
                                )
                            ),
                        ),
                    )

                    candidate = response.candidates[0]
                    content = candidate.content  # genai_types.Content

                    # Append Gemini's response (which may include tool calls)
                    # to the history so future turns have the full context.
                    history.append(content)

                    # ── Check for tool calls ───────────────────────────────────
                    # Gemini returns function_call parts when it wants to use a tool.
                    function_calls = [
                        part.function_call
                        for part in content.parts
                        if part.function_call is not None
                    ]

                    if not function_calls:
                        # No tool calls — Gemini produced a final text answer.
                        final_text = " ".join(
                            part.text for part in content.parts if part.text
                        )
                        print(f"\nAssistant: {final_text}\n")
                        break  # exit the inner agentic loop

                    # ── Execute tool calls via the gateway ─────────────────────
                    # Gemini may request multiple tool calls in a single response.
                    # We execute all of them and collect their results before
                    # sending them back together in one "tool" history entry.
                    tool_results = []

                    for fc in function_calls:
                        tool_name: str = fc.name
                        tool_args: dict = dict(fc.args) if fc.args else {}

                        print(f"  [Tool call] {tool_name}({tool_args})")

                        # Dispatch the call to the gateway, which routes it to
                        # the appropriate institution server.
                        try:
                            mcp_result = await mcp_session.call_tool(
                                tool_name, arguments=tool_args
                            )
                            # Join all text content items in the result.
                            result_text = "\n".join(
                                item.text
                                for item in mcp_result.content
                                if hasattr(item, "text")
                            )
                        except Exception as exc:
                            result_text = f"Tool error: {exc}"

                        print(f"  [Tool result] {result_text[:300]}")

                        # Build a Gemini FunctionResponse to feed back.
                        tool_results.append(
                            genai_types.Part(
                                function_response=genai_types.FunctionResponse(
                                    name=tool_name,
                                    response={"result": result_text},
                                )
                            )
                        )

                    # Append ALL tool results as a single "tool" content block.
                    # Gemini's API requires tool results to be grouped together
                    # in one Content with role="tool".
                    history.append(
                        genai_types.Content(
                            role="tool",
                            parts=tool_results,
                        )
                    )
                    # Continue the inner loop: Gemini will process the tool
                    # results and either call more tools or produce the final answer.


def main() -> None:
    """Entry point for  python agent/gemini_agent.py  or  python -m agent.gemini_agent."""
    asyncio.run(run_agent())


if __name__ == "__main__":
    main()
