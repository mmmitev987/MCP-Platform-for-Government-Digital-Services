"""
backend/services/chat_service.py
────────────────────────────────────────────────────────────────────────────────
Singleton ChatService supporting both OpenAI (GPT) and Google Gemini.

Switch provider via .env:
    LLM_PROVIDER=openai    → uses OPENAI_API_KEY + OPENAI_MODEL
    LLM_PROVIDER=gemini    → uses GEMINI_API_KEY + GEMINI_MODEL
"""

import asyncio
import json
import sys
from contextlib import AsyncExitStack
from datetime import datetime, timezone
from pathlib import Path

import yaml
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.activity import ActivityLog
from backend.models.chat import ChatSession, Message

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()
_GATEWAY_CONFIG_PATH = PROJECT_ROOT / "gateway" / "config.yaml"

# ── Provider SDK imports ───────────────────────────────────────────────────────
try:
    from openai import OpenAI, RateLimitError, APIStatusError
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    _GEMINI_AVAILABLE = True
except ImportError:
    _GEMINI_AVAILABLE = False

# ── Static system prompt sections ─────────────────────────────────────────────

_STATIC_PROMPT_PREFIX = """
You are a helpful assistant for Macedonian citizens interacting with government
online portals.

━━━ LANGUAGE — ALWAYS MATCH THE USER'S LANGUAGE ━━━

  Detect the language of each user message and reply in that same language.
  Apply this rule to every response, including clarifying questions, error
  messages, and tool result summaries.

  Examples:
    • User writes in Macedonian  → reply entirely in Macedonian.
    • User writes in English     → reply entirely in English.
    • User writes in Albanian    → reply entirely in Albanian.
    • User writes in Serbian     → reply entirely in Serbian.

  If you cannot reliably support the detected language, reply in English and
  add a polite note that the language is not fully supported.
  Never mix languages within a single response.
  Never default to English when the user wrote in another language.
""".strip()

_STATIC_PROMPT_SUFFIX = """
━━━ INTENT CLARIFICATION — ASK BEFORE YOU ACT ━━━

  Before calling ANY tool, you MUST be certain of the user's exact goal.
  If the request is ambiguous, incomplete, or could match more than one
  service or action, ask ONE focused clarifying question and wait for the
  answer. Never assume, never guess, never call a tool speculatively.

  A request is AMBIGUOUS when any of the following is true:
    • The topic matches multiple services with different requirements
      (e.g. "пасош" could be: first-time application, renewal, replacement
       after loss, or just asking about the fee — each needs different data).
    • A required argument is missing and cannot be inferred from context
      (e.g. asking for a doctor without mentioning a city or specialty;
       asking for appointments without a date).
    • The user asks about a company but does not say what they need
      (general info, founders, annual reports — these are separate tools).
    • The user asks about an education document without naming the type
      (enrollment certificate, diploma recognition, transcript, etc.).
    • The user's phrasing refers to more than one portal or institution.

  A request is CLEAR when:
    • The specific service, document type, or action is named explicitly.
    • All required arguments (city, date, company name, document type) are
      present or unambiguously inferable from the conversation so far.

  Rules for asking clarifying questions:
    • Ask ONLY ONE question per turn — the most important missing piece.
    • Make the question concrete: offer 2–4 specific options when possible.
      Example: "Дали сакате да поднесете барање за прв пат, или да го
       обновите постоечкиот пасош?"
    • Do NOT call any tool while waiting for the clarification.
    • Once the user answers, re-evaluate — if intent is now clear, proceed;
      if still ambiguous, ask one more follow-up before calling any tool.
    • Never ask for information that you can already infer from context.

━━━ GENERAL TOOL USAGE RULES ━━━

  NEVER call any tool for:
    • Greetings, small talk, or questions about your own capabilities.
    • Questions answerable from general knowledge ("what is a passport?").
    • When you need to clarify the user's intent — ask first, then call tools.

  Avoid redundant calls:
    • If a tool already returned enough information, do NOT call more tools.
    • Never call the same tool twice with the same arguments.
    • Never call a "details" tool unless the user explicitly needs details.

━━━ TOOL ERROR HANDLING ━━━

  When a tool returns { "error": true, "code": "...", "message": "..." }, write
  a short, warm, natural-language explanation — as if a helpful person is
  explaining a temporary inconvenience, not a system reporting a failure code.

  Error code → what to say (adapt freely to match the user's language and tone):
    "network_error"    → "The [portal name] portal isn't reachable right now —
                          it may be temporarily down. You can try again in a
                          few minutes."
    "auth_required"    → "You'll need to log in first before I can look that up.
                          Would you like me to open the login page for you?"
    "not_found"        → "I couldn't find that on the portal. It may not exist
                          or the name might be slightly different — could you
                          double-check the details?"
    "adapter_down"     → "The [portal name] portal is currently starting up and
                          isn't ready yet. Please try again in a moment."
    "browser_error"    → "I wasn't able to open the browser window needed for
                          this. Please try again — if it keeps happening, let
                          me know."
    "unexpected_error" → "Something unexpected went wrong while checking that.
                          I'd suggest trying again in a little while."

  Rules that always apply:
    • DO NOT retry the same tool call — explain the situation, then stop.
    • NEVER mention error codes, HTTP status codes, "tool", "adapter", "MCP",
      "subprocess", "exception", or any other technical term.
    • NEVER show raw exception text or stack traces.
    • Keep the message to 1–3 sentences. Offer a concrete next step when possible.

━━━ FACTUAL GROUNDING — NEVER FABRICATE ━━━

  Every piece of information you give about a government service, document,
  deadline, fee, requirement, or institution MUST come from a tool result
  returned in this conversation. No exceptions.

  Specifically, you MUST NOT:
    • Invent, guess, or approximate fees, deadlines, or processing times.
    • List required documents that were not returned by a tool.
    • Name services, portals, or legal acts from general knowledge.
    • State that a service "usually takes X days" or "typically costs X" without
      a tool result confirming it for this specific service.
    • Fill gaps in tool results with information from your training data.

  What to do instead:
    • If no tool has been called yet, call the appropriate tool before answering.
    • If a tool returned no data for a field (null, empty list, missing key),
      tell the user that information is not available on the portal right now.
    • If you are unsure whether a detail came from a tool or from memory, do not
      include it — say "I don't have that information from the portal."
    • Never paraphrase or reinterpret tool output in a way that changes its meaning.

━━━ CONSISTENCY — IDENTICAL QUESTIONS MUST GIVE IDENTICAL ANSWERS ━━━

  When a tool returns data about a service, document, or deadline, your response
  MUST be fully reproducible. Two users asking the same question must receive
  the same information. To guarantee this:

  • Report ALL factual fields returned by the tool — never omit fees, deadlines,
    required documents, or conditions based on what seems "more important".
  • Use the EXACT values from the tool: do not round amounts, shorten names,
    or reword conditions. If the tool says "1 500 MKD", write "1 500 MKD".
  • Use a FIXED structure for each type of answer:
      – Service requirements: name → required documents → fees → deadline → apply link.
      – Doctor/appointment: doctor name → clinic → city → available slots.
      – Company info: legal name → registration number → status → address → activity.
  • If a field is null or absent in the tool result, write "not specified" or
    "not available" — never silently drop it from the response.
  • Do NOT add caveats, qualifications, or context from general knowledge that
    could differ between runs (e.g. "this may vary", "typically around X").

━━━ SECURITY & RESPONSE RULES ━━━

  1. NEVER ask the user for passwords or credentials.
  2. NEVER repeat cookies, tokens, or auth headers in responses.
  3. Keep responses concise and in plain language. Use bullet points for lists.
  4. If the user asks about something outside the connected portals, briefly explain
     your scope, offer 2-3 concrete things you CAN help with, and end with a question.
""".strip()


def _build_system_prompt(connected_slugs: list[str]) -> str:
    """
    Build the full system prompt from gateway/config.yaml.
    Only includes institutions that are actually connected (alive).
    """
    try:
        with open(_GATEWAY_CONFIG_PATH) as f:
            config = yaml.safe_load(f)
    except Exception as exc:
        print(f"[ChatService] Warning: could not read gateway config: {exc}", file=sys.stderr)
        config = {"institutions": []}

    institutions = [
        inst for inst in config.get("institutions", [])
        if inst["slug"] in connected_slugs
    ]

    if not institutions:
        return _STATIC_PROMPT_PREFIX + "\n\n" + _STATIC_PROMPT_SUFFIX

    lines = [_STATIC_PROMPT_PREFIX, "", "You have access to MCP tools for the following institutions:", ""]
    for i, inst in enumerate(institutions, 1):
        slug = inst["slug"]
        name = inst["name"]
        desc = inst.get("description", "").strip().replace("\n", " ")
        lines.append(f"  {i}. {name}  (prefix: {slug}__)")
        if desc:
            lines.append(f"     {desc}")
        lines.append("")

    lines += ["━━━ INSTITUTION-SPECIFIC TOOL RULES ━━━", ""]
    for inst in institutions:
        slug = inst["slug"]
        name = inst["name"]
        rules: list[str] = inst.get("tool_rules", [])
        lines.append(f"  {name.upper()} (prefix: {slug}__):")
        for rule in rules:
            lines.append(f"    • {rule}")
        lines.append("")

    lines += ["", _STATIC_PROMPT_SUFFIX]
    return "\n".join(lines)


# ── Tool schema converters ─────────────────────────────────────────────────────

def _mcp_tool_to_openai_function(mcp_tool) -> dict:
    """Convert an MCP tool definition to OpenAI function-calling format."""
    input_schema = mcp_tool.inputSchema or {}
    return {
        "type": "function",
        "function": {
            "name": mcp_tool.name,
            "description": mcp_tool.description or "",
            "parameters": {
                "type": "object",
                "properties": input_schema.get("properties", {}),
                "required": input_schema.get("required", []),
            },
        },
    }


def _mcp_tool_to_gemini_function(mcp_tool):
    """Convert an MCP tool definition to a Gemini FunctionDeclaration."""
    input_schema = mcp_tool.inputSchema or {}
    properties_raw = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    gemini_properties = {}
    for param_name, param_schema in properties_raw.items():
        json_type = param_schema.get("type", "string").upper()
        gemini_type = getattr(_genai_types.Type, json_type, _genai_types.Type.STRING)
        gemini_properties[param_name] = _genai_types.Schema(
            type=gemini_type,
            description=param_schema.get("description", ""),
        )

    parameters = _genai_types.Schema(
        type=_genai_types.Type.OBJECT,
        properties=gemini_properties,
        required=required,
    )

    return _genai_types.FunctionDeclaration(
        name=mcp_tool.name,
        description=mcp_tool.description or "",
        parameters=parameters,
    )


# ── ChatService ────────────────────────────────────────────────────────────────

class ChatService:
    def __init__(self):
        self._mcp_session: ClientSession | None = None
        self._exit_stack: AsyncExitStack | None = None
        self._system_prompt: str = ""

        # OpenAI state
        self._openai_client: "OpenAI | None" = None
        self._all_tools_openai: list[dict] = []

        # Gemini state
        self._gemini_client = None
        self._all_declarations_gemini: list = []

        # Per-session conversation histories (keyed by session_id)
        # OpenAI: list of dicts  |  Gemini: list of Content objects
        self._histories_openai: dict[int, list[dict]] = {}
        self._histories_gemini: dict[int, list] = {}

        # Per-user locks + global concurrency cap
        self._locks: dict[int, asyncio.Lock] = {}
        self._ai_semaphore = asyncio.Semaphore(10)

    # ── Tool filtering ─────────────────────────────────────────────────────────

    def _build_tools_openai(self, disabled: set[str]) -> list[dict]:
        return [
            t for t in self._all_tools_openai
            if not any(t["function"]["name"].startswith(f"{slug}__") for slug in disabled)
        ]

    def _build_tools_gemini(self, disabled: set[str]) -> list:
        declarations = [
            fd for fd in self._all_declarations_gemini
            if not any(fd.name.startswith(f"{slug}__") for slug in disabled)
        ]
        return [_genai_types.Tool(function_declarations=declarations)]

    # ── Lock helpers ───────────────────────────────────────────────────────────

    def _get_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    # ── Startup / shutdown ─────────────────────────────────────────────────────

    async def start(self) -> None:
        provider = settings.LLM_PROVIDER.lower()

        if provider == "gemini" and not _GEMINI_AVAILABLE:
            raise RuntimeError("LLM_PROVIDER=gemini but google-genai is not installed. Run: pip install google-genai")
        if provider == "openai" and not _OPENAI_AVAILABLE:
            raise RuntimeError("LLM_PROVIDER=openai but openai is not installed. Run: pip install openai")

        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gateway.main"],
            cwd=str(PROJECT_ROOT),
        )
        read, write = await self._exit_stack.enter_async_context(stdio_client(server_params))
        self._mcp_session = await self._exit_stack.enter_async_context(ClientSession(read, write))
        await self._mcp_session.initialize()

        tools_response = await self._mcp_session.list_tools()

        if provider == "gemini":
            self._all_declarations_gemini = [_mcp_tool_to_gemini_function(t) for t in tools_response.tools]
            self._gemini_client = _genai.Client(api_key=settings.GEMINI_API_KEY)
        else:
            self._all_tools_openai = [_mcp_tool_to_openai_function(t) for t in tools_response.tools]
            self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)

        connected_slugs = list({
            t.name.split("__")[0]
            for t in tools_response.tools
            if "__" in t.name
        })
        self._system_prompt = _build_system_prompt(connected_slugs)

        print(
            f"[ChatService] Provider={provider.upper()} | "
            f"{len(tools_response.tools)} tools from: {connected_slugs}",
            file=sys.stderr,
        )

    async def stop(self) -> None:
        if self._exit_stack:
            await self._exit_stack.__aexit__(None, None, None)

    # ── History loaders ────────────────────────────────────────────────────────

    def _load_history_openai(self, session_id: int, db: Session) -> list[dict]:
        """Return (and cache) the OpenAI-format history for a session."""
        if session_id in self._histories_openai:
            return self._histories_openai[session_id]

        from sqlalchemy.orm import joinedload
        db_session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .options(joinedload(ChatSession.messages))
            .first()
        )
        history: list[dict] = []
        if db_session:
            for msg in sorted(db_session.messages, key=lambda m: m.created_at):
                history.append({"role": msg.role, "content": msg.content})

        self._histories_openai[session_id] = history
        return history

    def _load_history_gemini(self, session_id: int, db: Session) -> list:
        """Return (and cache) the Gemini-format history for a session."""
        if session_id in self._histories_gemini:
            return self._histories_gemini[session_id]

        from sqlalchemy.orm import joinedload
        db_session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .options(joinedload(ChatSession.messages))
            .first()
        )
        history: list = []
        if db_session:
            for msg in sorted(db_session.messages, key=lambda m: m.created_at):
                # DB stores role as "user" or "assistant"; Gemini uses "user" / "model"
                gemini_role = "model" if msg.role == "assistant" else "user"
                history.append(
                    _genai_types.Content(
                        role=gemini_role,
                        parts=[_genai_types.Part(text=msg.content)],
                    )
                )

        self._histories_gemini[session_id] = history
        return history

    # ── Agentic loop — OpenAI ──────────────────────────────────────────────────

    async def _agentic_loop_openai(
        self,
        history: list[dict],
        openai_tools: list[dict],
        user_id: int,
        db,
    ) -> tuple[str, list[str], dict | None]:
        portal_errors: list[str] = []
        geometry: dict | None = None

        while True:
            messages_to_send = [{"role": "system", "content": self._system_prompt}] + history

            try:
                response = await asyncio.to_thread(
                    self._openai_client.chat.completions.create,
                    model=settings.OPENAI_MODEL,
                    messages=messages_to_send,
                    tools=openai_tools if openai_tools else None,
                    tool_choice="auto" if openai_tools else None,
                    temperature=0,
                    seed=0,
                    timeout=settings.RESPONSE_TIMEOUT - 1,
                )
            except RateLimitError:
                return "Rate limit reached. Please wait a few seconds and try again.", [], geometry
            except APIStatusError as e:
                if e.status_code == 503:
                    return "The AI model is currently experiencing high demand. Please try again in a moment.", [], geometry
                raise

            choice = response.choices[0]
            assistant_msg = choice.message

            assistant_dict: dict = {"role": "assistant", "content": assistant_msg.content or ""}
            if assistant_msg.tool_calls:
                assistant_dict["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in assistant_msg.tool_calls
                ]
            history.append(assistant_dict)

            if not assistant_msg.tool_calls:
                raw = assistant_msg.content or ""
                text = raw if isinstance(raw, str) else (
                    " ".join(b.text for b in raw if hasattr(b, "text")) if isinstance(raw, list) else str(raw)
                )
                return text, portal_errors, geometry

            # Execute tool calls
            for tc in assistant_msg.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                try:
                    mcp_result = await self._mcp_session.call_tool(tool_name, arguments=tool_args)
                    result_text = "\n".join(
                        item.text for item in mcp_result.content if hasattr(item, "text")
                    )
                    try:
                        parsed = json.loads(result_text)
                        is_error = (
                            isinstance(parsed, dict) and parsed.get("error") is True
                        ) or (
                            isinstance(parsed, list) and len(parsed) == 1
                            and isinstance(parsed[0], dict) and parsed[0].get("error") is True
                        )
                        tool_status = "failed" if is_error else "completed"
                        if is_error:
                            service = tool_name.split("__")[0] if "__" in tool_name else None
                            if service and service not in portal_errors:
                                portal_errors.append(service)
                        # Capture katastar geometry for mini-map
                        if (
                            not is_error
                            and tool_name == "katastar__search_property"
                            and isinstance(parsed, dict)
                            and parsed.get("geometry")
                        ):
                            geometry = parsed["geometry"]
                    except (json.JSONDecodeError, TypeError):
                        tool_status = "completed"
                except Exception as exc:
                    result_text = json.dumps({
                        "error": True,
                        "code": "unexpected_error",
                        "message": f"Tool call failed: {exc}",
                    })
                    tool_status = "failed"

                service = tool_name.split("__")[0] if "__" in tool_name else "general"
                db.add(ActivityLog(
                    user_id=user_id,
                    service=service,
                    action=tool_name,
                    status=tool_status,
                    description=result_text[:500],
                ))

                history.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result_text,
                })

    # ── Agentic loop — Gemini ──────────────────────────────────────────────────

    async def _agentic_loop_gemini(
        self,
        history: list,
        gemini_tools: list,
        user_id: int,
        db,
    ) -> tuple[str, list[str], dict | None]:
        portal_errors: list[str] = []
        geometry: dict | None = None

        while True:
            try:
                response = await asyncio.to_thread(
                    self._gemini_client.models.generate_content,
                    model=settings.GEMINI_MODEL,
                    contents=history,
                    config=_genai_types.GenerateContentConfig(
                        system_instruction=self._system_prompt,
                        tools=gemini_tools,
                        temperature=0,
                        tool_config=_genai_types.ToolConfig(
                            function_calling_config=_genai_types.FunctionCallingConfig(
                                mode="AUTO"
                            )
                        ),
                    ),
                )
            except Exception as e:
                err = str(e).lower()
                if "quota" in err or "rate" in err or "429" in err:
                    return "Rate limit reached. Please wait a few seconds and try again.", [], geometry
                if "503" in err or "unavailable" in err:
                    return "The AI model is currently experiencing high demand. Please try again in a moment.", [], geometry
                raise

            candidate = response.candidates[0]
            content = candidate.content  # genai_types.Content (role="model")

            # Append model's full response (may include function_call parts)
            history.append(content)

            # Check for function calls
            function_calls = [
                part.function_call
                for part in content.parts
                if part.function_call is not None
            ]

            if not function_calls:
                # Plain text response — done
                final_text = " ".join(
                    part.text for part in content.parts if part.text
                )
                return final_text, portal_errors, geometry

            # Execute all tool calls, collect results
            tool_result_parts = []
            for fc in function_calls:
                tool_name: str = fc.name
                tool_args: dict = dict(fc.args) if fc.args else {}

                try:
                    mcp_result = await self._mcp_session.call_tool(tool_name, arguments=tool_args)
                    result_text = "\n".join(
                        item.text for item in mcp_result.content if hasattr(item, "text")
                    )
                    try:
                        parsed = json.loads(result_text)
                        is_error = (
                            isinstance(parsed, dict) and parsed.get("error") is True
                        ) or (
                            isinstance(parsed, list) and len(parsed) == 1
                            and isinstance(parsed[0], dict) and parsed[0].get("error") is True
                        )
                        tool_status = "failed" if is_error else "completed"
                        if is_error:
                            service = tool_name.split("__")[0] if "__" in tool_name else None
                            if service and service not in portal_errors:
                                portal_errors.append(service)
                        # Capture katastar geometry for mini-map
                        if (
                            not is_error
                            and tool_name == "katastar__search_property"
                            and isinstance(parsed, dict)
                            and parsed.get("geometry")
                        ):
                            geometry = parsed["geometry"]
                    except (json.JSONDecodeError, TypeError):
                        tool_status = "completed"
                except Exception as exc:
                    result_text = json.dumps({
                        "error": True,
                        "code": "unexpected_error",
                        "message": f"Tool call failed: {exc}",
                    })
                    tool_status = "failed"

                service = tool_name.split("__")[0] if "__" in tool_name else "general"
                db.add(ActivityLog(
                    user_id=user_id,
                    service=service,
                    action=tool_name,
                    status=tool_status,
                    description=result_text[:500],
                ))

                tool_result_parts.append(
                    _genai_types.Part(
                        function_response=_genai_types.FunctionResponse(
                            name=tool_name,
                            response={"result": result_text},
                        )
                    )
                )

            # All tool results go in one Content block with role="tool"
            history.append(
                _genai_types.Content(
                    role="tool",
                    parts=tool_result_parts,
                )
            )

    # ── Public chat method ─────────────────────────────────────────────────────

    async def chat(
        self,
        user_id: int,
        message: str,
        db: Session,
        session_id: int | None = None,
        disabled_institutions: set[str] | None = None,
    ) -> tuple[str, int, list[str], dict | None]:
        """
        Process a user message through the AI agent and return the response.

        Args:
            user_id: Database ID of the user sending the message.
            message: The user's message text.
            db: SQLAlchemy database session.
            session_id: Optional existing chat session ID to continue.
            disabled_institutions: Optional set of institution slugs to exclude from tools.

        Returns:
            A 4-tuple containing:
            - final_text (str): The AI's final response text.
            - session_id (int): The chat session ID (new or existing).
            - portal_errors (list[str]): List of institution slugs that had tool failures.
            - geometry (dict | None): Optional map geometry data from katastar tools,
                                      format: { polygon: [[lat,lon],...], centroid: [lat,lon] }
        """
        assert self._mcp_session is not None, "ChatService.start() was not called"

        provider = settings.LLM_PROVIDER.lower()

        # Resolve or create the DB chat session
        is_new_session = session_id is None
        if session_id:
            chat_session = db.query(ChatSession).filter(
                ChatSession.id == session_id,
                ChatSession.user_id == user_id,
            ).first()
            if not chat_session:
                raise ValueError("Session not found")
        else:
            chat_session = ChatSession(user_id=user_id, title=message[:60])
            db.add(chat_session)
            db.commit()
            db.refresh(chat_session)
            self._histories_openai[chat_session.id] = []
            self._histories_gemini[chat_session.id] = []

        # Save user message to DB immediately
        db.add(Message(session_id=chat_session.id, role="user", content=message))
        db.commit()

        final_text = ""
        portal_errors: list[str] = []
        geometry: dict | None = None

        async with self._get_lock(user_id):
            if provider == "gemini":
                gemini_tools = self._build_tools_gemini(disabled_institutions or set())
                history = self._load_history_gemini(chat_session.id, db)
                history.append(
                    _genai_types.Content(
                        role="user",
                        parts=[_genai_types.Part(text=message)],
                    )
                )
                try:
                    async with self._ai_semaphore:
                        final_text, portal_errors, geometry = await asyncio.wait_for(
                            self._agentic_loop_gemini(history, gemini_tools, user_id, db),
                            timeout=settings.RESPONSE_TIMEOUT,
                        )
                except asyncio.TimeoutError:
                    final_text = (
                        "⏱️ The request took too long to process. "
                        "Please try again or rephrase your question."
                    )
            else:
                openai_tools = self._build_tools_openai(disabled_institutions or set())
                history = self._load_history_openai(chat_session.id, db)
                history.append({"role": "user", "content": message})
                try:
                    async with self._ai_semaphore:
                        final_text, portal_errors, geometry = await asyncio.wait_for(
                            self._agentic_loop_openai(history, openai_tools, user_id, db),
                            timeout=settings.RESPONSE_TIMEOUT,
                        )
                except asyncio.TimeoutError:
                    final_text = (
                        "⏱️ The request took too long to process. "
                        "Please try again or rephrase your question."
                    )

        db.commit()

        # Save assistant reply to DB
        db.add(Message(session_id=chat_session.id, role="assistant", content=final_text))
        db.commit()

        # Generate a short title from the first message
        if is_new_session:
            try:
                if provider == "gemini":
                    title_response = await asyncio.to_thread(
                        self._gemini_client.models.generate_content,
                        model=settings.GEMINI_MODEL,
                        contents=[
                            _genai_types.Content(
                                role="user",
                                parts=[_genai_types.Part(
                                    text=(
                                        "Generate a short chat title (3-5 words, no quotes, no punctuation) "
                                        "that summarises what the user is asking about. "
                                        "Reply with only the title.\n\nUser message: " + message
                                    )
                                )],
                            )
                        ],
                    )
                    chat_session.title = title_response.text.strip()[:60]
                else:
                    title_response = await asyncio.to_thread(
                        self._openai_client.chat.completions.create,
                        model=settings.OPENAI_MODEL,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "Generate a short chat title (3-5 words, no quotes, no punctuation) "
                                    "that summarises what the user is asking about. Reply with only the title."
                                ),
                            },
                            {"role": "user", "content": message},
                        ],
                    )
                    chat_session.title = title_response.choices[0].message.content.strip()[:60]
                db.commit()
            except Exception:
                pass

        return final_text, chat_session.id, portal_errors, geometry


# Module-level singleton imported by routers
chat_service = ChatService()
