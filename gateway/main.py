"""
gateway/main.py
────────────────────────────────────────────────────────────────────────────────
MCP Aggregator Gateway — the single entry point for the Gemini agent.

What this does
──────────────
The gateway is itself an MCP server.  Instead of implementing its own tools,
it aggregates tools from multiple institution-specific MCP servers:

  ┌─────────────────────────────────────────────────────────────────┐
  │                   agent/gemini_agent.py                         │
  └──────────────────────────────┬──────────────────────────────────┘
                                 │ MCP stdio  (one connection)
                                 ▼
  ┌─────────────────────────────────────────────────────────────────┐
  │                    gateway/main.py   ◄── YOU ARE HERE           │
  │                                                                 │
  │   • Reads gateway/config.yaml (institution registry).          │
  │   • Spawns each institution server as a subprocess.             │
  │   • Collects & namespaces their tools:                          │
  │       uslugi__login, mojtermin__get_doctors_by_city …           │
  │   • Routes incoming tool calls to the correct subprocess.       │
  └──────────────────┬──────────────────────────┬───────────────────┘
      MCP stdio       │                          │  MCP stdio
                      ▼                          ▼
      institutions/uslugi/main.py   institutions/mojtermin/main.py

Why the low-level MCP Server API?
──────────────────────────────────
FastMCP registers tools with Python decorators at import time, so it is not
suitable for DYNAMIC tool registration (we don't know what tools exist until
we connect to the institution servers at runtime).  The low-level
`mcp.server.lowlevel.Server` API lets us register list_tools and call_tool
handlers that compute their responses dynamically — perfect for a proxy.

Startup sequence
────────────────
  1. Read gateway/config.yaml.
  2. For each institution: spawn subprocess, connect via MCP, call list_tools().
  3. Build the aggregated tool list (with namespaced names).
  4. Open the gateway's own stdio transport and start serving the agent.

All institution subprocess connections are kept alive inside an AsyncExitStack
for the entire lifetime of the gateway process.

Running
───────
  python -m gateway.main          # normal (agent spawns this)
  python gateway/main.py          # also works
"""

import asyncio
import sys
from contextlib import AsyncExitStack
from pathlib import Path

import yaml  # PyYAML — add to requirements.txt

# ── Low-level MCP server API ──────────────────────────────────────────────────
# We use the low-level Server instead of FastMCP because we need to register
# tool handlers dynamically (we don't know tool names at import time).
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# ── MCP client API — used to connect to institution subprocesses ──────────────
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# ── Institution registry ──────────────────────────────────────────────────────
# Loaded once at module import so the config is available before async starts.
_config_path = Path(__file__).parent / "config.yaml"
with open(_config_path) as _f:
    _gateway_config: dict = yaml.safe_load(_f)


# ═══════════════════════════════════════════════════════════════════════════════
# GatewayServer
# ═══════════════════════════════════════════════════════════════════════════════

class GatewayServer:
    """
    Aggregator MCP server.

    Maintains live MCP client sessions to all institution servers and presents
    their combined tool set to the agent under namespaced names.

    Attributes:
        _server:        The low-level MCP Server that serves the agent.
        _sessions:      slug → ClientSession mapping for routing.
        _tool_routing:  namespaced_tool_name → institution slug mapping.
        _tools:         Complete list of namespaced Tool objects for list_tools.
    """

    def __init__(self):
        # Create the low-level MCP Server.
        # "mcp-gateway" is the server name sent during the MCP handshake.
        self._server = Server("mcp-gateway")

        # Populated during connect_institutions():
        self._sessions: dict[str, ClientSession] = {}       # slug → session
        self._tool_routing: dict[str, str] = {}             # namespaced name → slug
        self._tools: list[types.Tool] = []                  # all namespaced tools

        # Register the two MCP request handlers on the server.
        # Using decorators here keeps the handler registration close to where
        # the server object is created — easy to find.
        self._server.list_tools()(self._handle_list_tools)
        self._server.call_tool()(self._handle_call_tool)

    # ── MCP request handlers ──────────────────────────────────────────────────

    async def _handle_list_tools(self) -> list[types.Tool]:
        """
        Respond to the agent's tools/list request.

        Returns the aggregated list of all namespaced tools from every
        institution server.  Called once during the agent's initialisation
        and potentially again if the agent refreshes its tool list.
        """
        return self._tools

    async def _handle_call_tool(
        self,
        name: str,
        arguments: dict,
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Route an incoming tool call to the correct institution server.

        Args:
            name:      Namespaced tool name, e.g. "uslugi__login".
            arguments: Dict of tool arguments from the LLM.

        Returns:
            List of MCP content items (usually a single TextContent).
        """
        # Look up which institution owns this tool.
        slug = self._tool_routing.get(name)

        if slug is None:
            # This should never happen if list_tools() is consistent, but
            # guard against it so the agent gets a meaningful error message.
            return [types.TextContent(
                type="text",
                text=f"Gateway error: unknown tool '{name}'. "
                     f"Known tools: {list(self._tool_routing.keys())}",
            )]

        # Strip the "slug__" prefix to get the original tool name that the
        # institution server registered.
        # e.g.  "uslugi__login"  →  prefix="uslugi__"  →  original="login"
        prefix = f"{slug}__"
        original_name = name[len(prefix):]

        # Retrieve the live session for this institution.
        session = self._sessions[slug]

        print(f"[Gateway] Routing  {name}  →  {slug}:{original_name}  args={arguments}")

        # Delegate the call to the institution server.
        try:
            result = await session.call_tool(original_name, arguments=arguments)
            # result.content is already a list of MCP content items.
            return result.content

        except Exception as exc:
            # Surface institution-level errors as a text message so the LLM
            # can decide how to handle them (e.g., suggest re-logging in).
            error_msg = f"Institution '{slug}' returned an error for '{original_name}': {exc}"
            print(f"[Gateway] ERROR: {error_msg}")
            return [types.TextContent(type="text", text=error_msg)]

    # ── Institution connection management ─────────────────────────────────────

    async def connect_institutions(self, exit_stack: AsyncExitStack) -> None:
        """
        Spawn all institution servers as subprocesses and connect to them.

        For each institution in config.yaml:
          1. Build StdioServerParameters (command + args + working dir).
          2. Use stdio_client() to spawn the subprocess and create IO streams.
          3. Wrap those streams in a ClientSession and call initialize().
          4. Fetch the tool list, namespace the names, and record routing.

        All context managers (stdio_client, ClientSession) are pushed onto the
        provided AsyncExitStack so they stay alive until the stack unwinds at
        the end of run() — i.e., when the agent disconnects and the gateway exits.

        Args:
            exit_stack: An open AsyncExitStack that owns the subprocess lifetimes.
        """
        institutions_config: list[dict] = _gateway_config.get("institutions", [])

        if not institutions_config:
            print("[Gateway] WARNING: No institutions defined in gateway/config.yaml.")
            return

        for inst in institutions_config:
            slug: str = inst["slug"]
            display_name: str = inst["name"]

            # The config says "python" — replace it with the same interpreter
            # that is running the gateway so we always use the venv Python,
            # not whatever "python" resolves to on the system PATH.
            raw_command: str = inst["command"]
            command = sys.executable if raw_command in ("python", "python3") else raw_command
            args: list[str] = inst.get("args", [])

            print(f"[Gateway] Connecting to institution: {display_name} ({slug})")
            print(f"[Gateway]   Command: {command} {' '.join(args)}")

            # ── Spawn the institution subprocess ──────────────────────────────
            # StdioServerParameters tells the MCP client how to launch the
            # server process.  cwd=PROJECT_ROOT ensures that module-level
            # imports (e.g. "from institutions.uslugi...") resolve correctly.
            server_params = StdioServerParameters(
                command=command,
                args=args,
                cwd=str(PROJECT_ROOT),
            )

            # stdio_client() is an async context manager that:
            #   • Spawns the subprocess.
            #   • Creates asyncio.Queue-based read/write streams over the pipes.
            #   • On exit: closes the streams and terminates the subprocess.
            #
            # We push it onto exit_stack so the subprocess lives as long as
            # the gateway itself.
            read_stream, write_stream = await exit_stack.enter_async_context(
                stdio_client(server_params)
            )

            # ── Wrap in an MCP ClientSession ──────────────────────────────────
            # ClientSession handles the MCP JSON-RPC protocol: it sends
            # "initialize" on entry and "close" on exit.
            session = await exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )

            # Perform the MCP handshake (sends initialize, waits for response).
            await session.initialize()

            # ── Fetch and namespace the institution's tools ───────────────────
            tools_response = await session.list_tools()

            institution_tool_count = len(tools_response.tools)

            for tool in tools_response.tools:
                # Build the namespaced name: "uslugi__login", "mojtermin__get_doctors_by_city" …
                namespaced_name = f"{slug}__{tool.name}"

                # Record which institution handles this tool for routing.
                self._tool_routing[namespaced_name] = slug

                # Create a new Tool object with:
                #   • The namespaced name (what the LLM will call).
                #   • A description prefixed with "[PortalName] " so the LLM
                #     knows which institution this tool interacts with.
                #   • The original input schema (parameter definitions unchanged).
                namespaced_tool = types.Tool(
                    name=namespaced_name,
                    description=f"[{display_name}] {tool.description or ''}",
                    inputSchema=tool.inputSchema,
                )
                self._tools.append(namespaced_tool)

            # Store the live session for later routing in _handle_call_tool.
            self._sessions[slug] = session

            print(
                f"[Gateway] ✓ {display_name}: "
                f"{institution_tool_count} tools registered "
                f"({', '.join(t.name for t in tools_response.tools)})"
            )

        total = len(self._tools)
        institutions_count = len(self._sessions)
        print(
            f"\n[Gateway] Ready — {total} tools aggregated "
            f"from {institutions_count} institution(s).\n"
        )

    # ── Main run loop ─────────────────────────────────────────────────────────

    async def run(self) -> None:
        """
        Full gateway lifecycle:
          1. Connect to all institution servers (spawn subprocesses).
          2. Open the gateway's own stdio transport to serve the agent.
          3. Block until the agent disconnects.
          4. Clean up all institution subprocess connections.
        """
        async with AsyncExitStack() as exit_stack:

            # ── Step 1: Connect to institution servers ────────────────────────
            # This spawns institution subprocesses and populates self._tools
            # and self._sessions before the agent ever sends a request.
            await self.connect_institutions(exit_stack)

            # ── Step 2: Open the gateway's own stdio transport ────────────────
            # stdio_server() creates an async context that reads from stdin and
            # writes to stdout using the asyncio-streams-based MCP transport.
            # This is the channel the agent (gemini_agent.py) communicates on.
            #
            # NOTE: At this point stdin IS the agent's connection.  We must not
            # read from stdin for any other purpose after this line.
            async with stdio_server() as (read_stream, write_stream):

                print("[Gateway] Stdio transport open — waiting for agent.")

                # ── Step 3: Run the MCP server protocol ───────────────────────
                # server.run() enters the JSON-RPC message loop:
                #   - Reads MCP requests from read_stream (agent → gateway).
                #   - Dispatches them to our registered handlers.
                #   - Writes responses to write_stream (gateway → agent).
                # This call blocks until the agent closes the connection.
                await self._server.run(
                    read_stream,
                    write_stream,
                    # create_initialization_options() builds the standard MCP
                    # server capabilities structure sent during the handshake.
                    self._server.create_initialization_options(),
                )

            # ── Step 4: Cleanup ───────────────────────────────────────────────
            # The AsyncExitStack unwinds here, closing all institution sessions
            # and terminating their subprocess (in reverse order of registration).
            print("[Gateway] Agent disconnected. Shutting down institution servers.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Run the gateway.  Called by  python -m gateway.main  or directly."""
    asyncio.run(GatewayServer().run())


if __name__ == "__main__":
    main()
