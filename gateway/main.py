"""
gateway/main.py
────────────────────────────────────────────────────────────────────────────────
MCP Aggregator Gateway — the single entry point for the AI agent.

What this does
──────────────
The gateway is itself an MCP server.  Instead of implementing its own tools,
it aggregates tools from multiple institution-specific MCP servers:

  ┌─────────────────────────────────────────────────────────────────┐
  │                   backend/services/chat_service.py              │
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
  │   • FAULT ISOLATION: one adapter crashing never affects others. │
  └──────────────────┬──────────────────────────┬───────────────────┘
      MCP stdio       │                          │  MCP stdio
                      ▼                          ▼
      institutions/uslugi/main.py   institutions/mojtermin/main.py

Fault isolation model
─────────────────────
Each institution runs in its own subprocess and is managed by an independent
InstitutionConnection object with its own AsyncExitStack.  Failures are
isolated at three levels:

  1. STARTUP: If an institution fails to connect on startup (e.g. import error,
     port conflict, Playwright crash), the gateway logs the error and continues
     connecting the remaining institutions.  The failed institution's tools are
     omitted from the tool list so the LLM never tries to call them.

  2. RUNTIME — dead session: If a tool call fails because the subprocess has
     crashed (pipe closed, OS error, MCP protocol error), the connection is
     marked dead and a structured error dict is returned to the LLM.  The
     other institutions are completely unaffected.

  3. RUNTIME — auto-reconnect: Before returning a failure to the LLM, the
     gateway makes one transparent reconnection attempt.  If the subprocess
     can be restarted (e.g., transient crash), the original tool call is
     retried and the LLM never sees an error.  If reconnection also fails,
     the LLM receives a structured { "error": true, "code": "adapter_down", … }
     response and can inform the user gracefully.

Startup sequence
────────────────
  1. Read gateway/config.yaml.
  2. For each institution: try to spawn subprocess + connect via MCP.
     On failure: log, continue with the rest.
  3. Build the aggregated tool list (with namespaced names).
  4. Open the gateway's own stdio transport and start serving the agent.

Running
───────
  python -m gateway.main          # normal (agent spawns this)
  python gateway/main.py          # also works
"""

import asyncio
import json
import sys
from contextlib import AsyncExitStack
from pathlib import Path

import yaml

# ── Low-level MCP server API ──────────────────────────────────────────────────
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
import mcp.types as types

# ── MCP client API ────────────────────────────────────────────────────────────
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ── Project root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# ── Institution registry ──────────────────────────────────────────────────────
_config_path = Path(__file__).parent / "config.yaml"
with open(_config_path) as _f:
    _gateway_config: dict = yaml.safe_load(_f)

# Timeout for a single institution connection attempt (seconds)
_CONNECT_TIMEOUT_S = 60


# ═══════════════════════════════════════════════════════════════════════════════
# InstitutionConnection — one per institution, fully isolated
# ═══════════════════════════════════════════════════════════════════════════════

class InstitutionConnection:
    """
    Manages the lifecycle of one institution's MCP subprocess.

    Each instance owns its own AsyncExitStack so it can be started and stopped
    independently of all other institutions.  This is the key to fault isolation:
    a crash in one InstitutionConnection cannot propagate to another.

    States
    ──────
      alive=True   — subprocess running, session ready, tools available
      alive=False  — failed to connect on startup OR subprocess has since died

    Thread/coroutine safety
    ───────────────────────
      _reconnect_lock prevents two concurrent callers from each trying to
      restart the same subprocess at the same time.
    """

    def __init__(self, slug: str, display_name: str, server_params: StdioServerParameters):
        self.slug = slug
        self.display_name = display_name
        self.server_params = server_params

        self.session: ClientSession | None = None
        self.tools: list[types.Tool] = []          # original (un-namespaced) tools
        self.alive: bool = False

        self._exit_stack: AsyncExitStack | None = None
        self._reconnect_lock = asyncio.Lock()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """
        Spawn the institution subprocess and establish an MCP session.

        Safe to call multiple times — tears down the previous connection first.

        Returns:
            True if connection succeeded and tools were fetched.
            False if any step failed (subprocess won't start, MCP error, etc.).
        """
        # Clean up any previous connection before attempting a new one.
        await self._teardown()

        try:
            self._exit_stack = AsyncExitStack()
            await self._exit_stack.__aenter__()

            read, write = await self._exit_stack.enter_async_context(
                stdio_client(self.server_params)
            )
            self.session = await self._exit_stack.enter_async_context(
                ClientSession(read, write)
            )

            await asyncio.wait_for(
                self.session.initialize(),
                timeout=_CONNECT_TIMEOUT_S,
            )

            tools_response = await asyncio.wait_for(
                self.session.list_tools(),
                timeout=_CONNECT_TIMEOUT_S,
            )
            self.tools = tools_response.tools
            self.alive = True

            print(
                f"[Gateway] ✓ {self.display_name}: "
                f"{len(self.tools)} tools registered "
                f"({', '.join(t.name for t in self.tools)})",
                file=sys.stderr,
            )
            return True

        except Exception as exc:
            print(
                f"[Gateway] ✗ {self.display_name} ({self.slug}): "
                f"connection failed — {type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            await self._teardown()
            return False

    async def _teardown(self) -> None:
        """Close the MCP session and terminate the subprocess (if running)."""
        if self._exit_stack is not None:
            try:
                await self._exit_stack.__aexit__(None, None, None)
            except Exception as exc:
                print(
                    f"[Gateway] Warning: error tearing down {self.slug}: {exc}",
                    file=sys.stderr,
                )
            finally:
                self._exit_stack = None
                self.session = None
                self.alive = False

    async def disconnect(self) -> None:
        """Gracefully shut down this institution's subprocess."""
        await self._teardown()

    # ── Tool call with auto-reconnect ─────────────────────────────────────────

    async def call_tool(
        self,
        name: str,
        arguments: dict,
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Call a tool on this institution's MCP server.

        If the call fails because the session is dead (subprocess crashed),
        one transparent reconnection attempt is made.  If that also fails,
        a structured error dict is returned as a TextContent so the LLM agent
        can inform the user gracefully.

        Args:
            name:      Original (un-namespaced) tool name as the institution
                       registered it, e.g. "login" not "uslugi__login".
            arguments: Tool arguments from the LLM.

        Returns:
            List of MCP content items on success.
            List with a single TextContent containing a JSON error dict on failure.
        """
        # ── First attempt ─────────────────────────────────────────────────────
        if self.alive and self.session is not None:
            try:
                result = await self.session.call_tool(name, arguments=arguments)
                return result.content
            except Exception as exc:
                print(
                    f"[Gateway] {self.slug}:{name} call failed "
                    f"({type(exc).__name__}: {exc}) — attempting reconnect",
                    file=sys.stderr,
                )
                self.alive = False  # Mark dead before reconnect attempt

        # ── Reconnect attempt (one per adapter, serialised by lock) ───────────
        async with self._reconnect_lock:
            # Another coroutine may have already reconnected while we waited.
            if self.alive and self.session is not None:
                try:
                    result = await self.session.call_tool(name, arguments=arguments)
                    return result.content
                except Exception:
                    self.alive = False

            print(
                f"[Gateway] Reconnecting to {self.display_name} ({self.slug}) …",
                file=sys.stderr,
            )
            reconnected = await self.connect()

        # ── Retry after reconnect ─────────────────────────────────────────────
        if reconnected and self.session is not None:
            try:
                result = await self.session.call_tool(name, arguments=arguments)
                print(
                    f"[Gateway] ✓ {self.slug} reconnected successfully.",
                    file=sys.stderr,
                )
                return result.content
            except Exception as exc:
                self.alive = False
                print(
                    f"[Gateway] {self.slug}:{name} failed even after reconnect: {exc}",
                    file=sys.stderr,
                )

        # ── All attempts exhausted — return structured error ──────────────────
        error_payload = json.dumps({
            "error": True,
            "code": "adapter_down",
            "message": (
                f"The {self.display_name} service is currently unavailable. "
                "It may be restarting — please try again in a moment."
            ),
        })
        return [types.TextContent(type="text", text=error_payload)]


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
        _connections:   slug → InstitutionConnection (one per institution).
        _tool_routing:  namespaced_tool_name → slug (for routing incoming calls).
        _tools:         Complete list of namespaced Tool objects for list_tools.
    """

    def __init__(self):
        self._server = Server("mcp-gateway")
        self._connections: dict[str, InstitutionConnection] = {}
        self._tool_routing: dict[str, str] = {}
        self._tools: list[types.Tool] = []

        self._server.list_tools()(self._handle_list_tools)
        self._server.call_tool()(self._handle_call_tool)

    # ── MCP request handlers ──────────────────────────────────────────────────

    async def _handle_list_tools(self) -> list[types.Tool]:
        """Return the aggregated list of all namespaced tools from every live institution."""
        return self._tools

    async def _handle_call_tool(
        self,
        name: str,
        arguments: dict,
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """
        Route an incoming tool call to the correct institution server.

        Fault isolation guarantee: exceptions from one institution cannot
        propagate here — they are caught inside InstitutionConnection.call_tool()
        and returned as structured error dicts.

        Args:
            name:      Namespaced tool name, e.g. "uslugi__login".
            arguments: Dict of tool arguments from the LLM.
        """
        slug = self._tool_routing.get(name)

        if slug is None:
            error_payload = json.dumps({
                "error": True,
                "code": "unknown_tool",
                "message": f"Unknown tool '{name}'. This is a gateway configuration error.",
            })
            return [types.TextContent(type="text", text=error_payload)]

        connection = self._connections[slug]

        # Strip the "slug__" prefix to get the original tool name.
        original_name = name[len(f"{slug}__"):]

        print(
            f"[Gateway] Routing  {name}  →  {slug}:{original_name}  "
            f"args={arguments}  alive={connection.alive}",
            file=sys.stderr,
        )

        # Delegate — fault isolation is inside InstitutionConnection.call_tool().
        return await connection.call_tool(original_name, arguments)

    # ── Institution connection management ─────────────────────────────────────

    async def connect_institutions(self) -> None:
        """
        Attempt to connect to every institution in config.yaml.

        FAULT ISOLATION: each institution is connected independently inside its
        own try/except.  A failure in one does NOT abort the others — the
        gateway continues with however many institutions succeeded.

        Institutions that fail to connect are excluded from the tool list.
        The LLM will not see their tools and cannot call them.  If the user
        asks about a service from a failed institution the LLM will answer
        from general knowledge or say it is unavailable.
        """
        institutions_config: list[dict] = _gateway_config.get("institutions", [])

        if not institutions_config:
            print("[Gateway] WARNING: No institutions defined in gateway/config.yaml.", file=sys.stderr)
            return

        # Connect to all institutions concurrently — faster startup and one
        # slow/hanging institution does not delay the others.
        connect_tasks = []
        for inst in institutions_config:
            slug: str = inst["slug"]
            display_name: str = inst["name"]
            raw_command: str = inst["command"]
            command = sys.executable if raw_command in ("python", "python3") else raw_command
            args: list[str] = inst.get("args", [])

            print(f"[Gateway] Connecting to institution: {display_name} ({slug})", file=sys.stderr)

            server_params = StdioServerParameters(
                command=command,
                args=args,
                cwd=str(PROJECT_ROOT),
            )

            conn = InstitutionConnection(slug, display_name, server_params)
            self._connections[slug] = conn
            connect_tasks.append(conn.connect())

        # gather() with return_exceptions=True means exceptions in individual
        # coroutines are returned as values, not raised — perfect for isolation.
        results = await asyncio.gather(*connect_tasks, return_exceptions=True)

        # Register tools from every institution that connected successfully.
        slugs = [inst["slug"] for inst in institutions_config]
        names = [inst["name"] for inst in institutions_config]

        for slug, display_name, result in zip(slugs, names, results):
            if isinstance(result, Exception):
                # gather() swallowed a raised exception — log and skip.
                print(
                    f"[Gateway] ✗ {display_name} ({slug}): "
                    f"unexpected exception — {result}",
                    file=sys.stderr,
                )
                continue

            conn = self._connections[slug]
            if not conn.alive:
                print(
                    f"[Gateway]   {display_name} tools EXCLUDED from aggregated list.",
                    file=sys.stderr,
                )
                continue

            for tool in conn.tools:
                namespaced_name = f"{slug}__{tool.name}"
                self._tool_routing[namespaced_name] = slug
                self._tools.append(types.Tool(
                    name=namespaced_name,
                    description=f"[{display_name}] {tool.description or ''}",
                    inputSchema=tool.inputSchema,
                ))

        alive_count = sum(1 for c in self._connections.values() if c.alive)
        total_count = len(self._connections)
        print(
            f"\n[Gateway] Ready — {len(self._tools)} tools aggregated "
            f"from {alive_count}/{total_count} institution(s).\n",
            file=sys.stderr,
        )

        if alive_count < total_count:
            failed = [
                f"{s} ({c.display_name})"
                for s, c in self._connections.items()
                if not c.alive
            ]
            print(
                f"[Gateway] ⚠ Failed institutions (tools excluded): {', '.join(failed)}",
                file=sys.stderr,
            )

    async def disconnect_institutions(self) -> None:
        """Gracefully tear down all institution subprocess connections."""
        await asyncio.gather(
            *(conn.disconnect() for conn in self._connections.values()),
            return_exceptions=True,  # never raise during shutdown
        )

    # ── Main run loop ─────────────────────────────────────────────────────────

    async def run(self) -> None:
        """
        Full gateway lifecycle:
          1. Connect to institution servers (concurrently, fault-isolated).
          2. Open the gateway's own stdio transport to serve the agent.
          3. Block until the agent disconnects.
          4. Clean up all institution subprocess connections.
        """
        # ── Step 1: Connect to institutions ───────────────────────────────────
        await self.connect_institutions()

        # ── Step 2 & 3: Open stdio transport and serve the agent ──────────────
        try:
            async with stdio_server() as (read_stream, write_stream):
                print("[Gateway] Stdio transport open — waiting for agent.", file=sys.stderr)
                await self._server.run(
                    read_stream,
                    write_stream,
                    self._server.create_initialization_options(),
                )
        finally:
            # ── Step 4: Cleanup ───────────────────────────────────────────────
            print("[Gateway] Agent disconnected. Shutting down institution servers.", file=sys.stderr)
            await self.disconnect_institutions()


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Run the gateway.  Called by  python -m gateway.main  or directly."""
    asyncio.run(GatewayServer().run())


if __name__ == "__main__":
    main()
