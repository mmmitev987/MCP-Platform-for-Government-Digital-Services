"""
backend/services/chat_service.py
────────────────────────────────────────────────────────────────────────────────
Singleton ChatService that owns the MCP gateway subprocess for the lifetime
of the FastAPI app. Refactored from agent/gemini_agent.py.
"""

import asyncio
import sys
from contextlib import AsyncExitStack
from datetime import datetime, timezone
from pathlib import Path

from google import genai
from google.genai import types as genai_types
from google.genai import errors as genai_errors
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from sqlalchemy.orm import Session

from backend.config import settings
from backend.models.activity import ActivityLog
from backend.models.chat import ChatSession, Message

PROJECT_ROOT = Path(__file__).parent.parent.parent.resolve()

SYSTEM_PROMPT = """
You are a helpful assistant for Macedonian citizens interacting with government
online portals.

You have access to MCP tools for TWO institutions:

  1. uslugi.gov.mk  — The main public services portal.
     Tools are prefixed with "uslugi__" (e.g. uslugi__login, uslugi__mvr_info_passport_renewal).
     Use these for: passport renewal info, document submissions, administrative procedures,
     ID cards, driving licenses, vehicle registration, citizenship, weapons permits, etc.

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


def _mcp_tool_to_gemini_function(mcp_tool) -> genai_types.FunctionDeclaration:
    input_schema = mcp_tool.inputSchema or {}
    properties_raw = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    gemini_properties: dict[str, genai_types.Schema] = {}
    for param_name, param_schema in properties_raw.items():
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


class ChatService:
    def __init__(self):
        self._mcp_session: ClientSession | None = None
        self._gemini_client: genai.Client | None = None
        self._gemini_tools: list[genai_types.Tool] = []
        self._exit_stack: AsyncExitStack | None = None
        # Per-user conversation histories: user_id → list[Content]
        self._histories: dict[int, list[genai_types.Content]] = {}
        # Per-user locks to guard history access across threads
        self._locks: dict[int, asyncio.Lock] = {}

    def _get_lock(self, user_id: int) -> asyncio.Lock:
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]

    async def start(self) -> None:
        self._exit_stack = AsyncExitStack()
        await self._exit_stack.__aenter__()

        server_params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gateway.main"],
            cwd=str(PROJECT_ROOT),
        )
        read, write = await self._exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self._mcp_session = await self._exit_stack.enter_async_context(
            ClientSession(read, write)
        )
        await self._mcp_session.initialize()

        tools_response = await self._mcp_session.list_tools()
        self._gemini_tools = [
            genai_types.Tool(
                function_declarations=[
                    _mcp_tool_to_gemini_function(t) for t in tools_response.tools
                ]
            )
        ]
        self._gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
        print(f"[ChatService] Gateway connected — {len(tools_response.tools)} tools available.", file=sys.stderr)

    async def stop(self) -> None:
        if self._exit_stack:
            await self._exit_stack.__aexit__(None, None, None)

    def _load_history(self, user_id: int, db: Session) -> list[genai_types.Content]:
        if user_id in self._histories:
            return self._histories[user_id]

        session = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .first()
        )
        history: list[genai_types.Content] = []
        if session:
            for msg in session.messages:
                history.append(genai_types.Content(
                    role="user" if msg.role == "user" else "model",
                    parts=[genai_types.Part(text=msg.content)],
                ))
        self._histories[user_id] = history
        return history

    async def chat(
        self,
        user_id: int,
        message: str,
        db: Session,
        session_id: int | None = None,
    ) -> tuple[str, int]:
        assert self._mcp_session is not None, "ChatService.start() was not called"

        # Resolve or create the DB chat session
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
            # Clear history for new session
            self._histories.pop(user_id, None)

        # Save user message to DB
        db.add(Message(session_id=chat_session.id, role="user", content=message))
        db.commit()

        async with self._get_lock(user_id):
            history = self._load_history(user_id, db)
            history.append(genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=message)],
            ))

            final_text = ""

            # Agentic inner loop — identical logic to gemini_agent.py
            while True:
                # Run the sync Gemini call in a thread to avoid blocking the event loop
                try:
                    response = await asyncio.to_thread(
                        self._gemini_client.models.generate_content,
                        model=settings.GEMINI_MODEL,
                        contents=history,
                        config=genai_types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            tools=self._gemini_tools,
                            tool_config=genai_types.ToolConfig(
                                function_calling_config=genai_types.FunctionCallingConfig(
                                    mode="AUTO"
                                )
                            ),
                        ),
                    )
                except genai_errors.ServerError as e:
                    if e.code == 503:
                        final_text = "The AI model is currently experiencing high demand. Please try again in a moment."
                        break
                    raise
                except genai_errors.ClientError as e:
                    if e.code == 429:
                        final_text = "Rate limit reached. Please wait a few seconds and try again."
                        break
                    raise

                candidate = response.candidates[0]
                content = candidate.content
                history.append(content)

                function_calls = [
                    p.function_call for p in content.parts if p.function_call
                ]

                if not function_calls:
                    final_text = " ".join(p.text for p in content.parts if p.text)
                    break

                tool_results = []
                for fc in function_calls:
                    tool_name = fc.name
                    tool_args = dict(fc.args) if fc.args else {}

                    try:
                        mcp_result = await self._mcp_session.call_tool(tool_name, arguments=tool_args)
                        result_text = "\n".join(
                            item.text for item in mcp_result.content if hasattr(item, "text")
                        )
                        tool_status = "completed"
                    except Exception as exc:
                        result_text = f"Tool error: {exc}"
                        tool_status = "failed"

                    # Log to activity
                    service = tool_name.split("__")[0] if "__" in tool_name else "general"
                    db.add(ActivityLog(
                        user_id=user_id,
                        service=service,
                        action=tool_name,
                        status=tool_status,
                        description=result_text[:500],
                    ))

                    tool_results.append(genai_types.Part(
                        function_response=genai_types.FunctionResponse(
                            name=tool_name,
                            response={"result": result_text},
                        )
                    ))

                history.append(genai_types.Content(role="tool", parts=tool_results))

        db.commit()

        # Save assistant reply to DB
        db.add(Message(session_id=chat_session.id, role="assistant", content=final_text))
        db.commit()

        return final_text, chat_session.id


# Module-level singleton imported by routers
chat_service = ChatService()
