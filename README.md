# MCP Platform for Government Digital Services

A full-stack web application that lets Macedonian citizens interact with government online portals through a conversational AI assistant. Built with FastAPI, React, and the Model Context Protocol (MCP).

---

## What It Does

Users log in to the web app, then chat with an AI assistant (powered by Google Gemini Flash) that can look up information and take actions on government portals on their behalf — passport renewal info, doctor appointments, pharmacist licensing, vehicle registration, and more.

The AI has no direct access to the portals. Instead, it calls **MCP tools** — structured functions that talk to each institution's API — and summarises the results in plain language.

---

## Architecture

```
Browser (React :3000)
    │  HTTP REST + JWT
    ▼
FastAPI (:8000)
    ├── /api/auth/*       — register, login, me
    ├── /api/chat/*       — send message, session history
    ├── /api/services/*   — list connected services
    ├── /api/activity/*   — paginated tool-call log
    └── /api/settings/*   — user profile & preferences
    │  in-process async call
    ▼
ChatService  (singleton, lives for the lifetime of the FastAPI process)
    │  MCP JSON-RPC over stdio
    ▼
gateway/main.py  (aggregates all institutions under namespaced tool names)
    │                          │
    ▼                          ▼
institutions/uslugi/       institutions/mojtermin/
main.py (88 tools)         main.py (6 tools)
```

Each institution server is a **FastMCP** process. The gateway spawns them as subprocesses on startup and multiplexes their tools under a `institutionname__toolname` namespace (e.g. `uslugi__mvr_info_passport_renewal`, `mojtermin__get_doctors_by_city`).

---

## Folder Structure

```
MCP-Platform-for-Government-Digital-Services/
│
├── backend/                        # FastAPI application
│   ├── main.py                     # App entry point, lifespan, CORS
│   ├── config.py                   # Settings from .env (API key, JWT secret, DB path)
│   ├── database.py                 # SQLAlchemy engine + get_db() dependency
│   ├── dependencies.py             # get_current_user() JWT dependency
│   ├── models/
│   │   ├── user.py                 # User table (email, hashed_password, preferences)
│   │   ├── chat.py                 # ChatSession + Message tables
│   │   └── activity.py            # ActivityLog table (one row per tool call)
│   ├── schemas/                    # Pydantic request/response schemas
│   ├── services/
│   │   ├── auth_service.py         # bcrypt hashing + JWT creation/decoding
│   │   └── chat_service.py         # ChatService singleton — owns the gateway subprocess
│   └── routers/
│       ├── auth.py                 # POST /api/auth/register, login, GET /api/auth/me
│       ├── chat.py                 # POST /api/chat, GET /api/chat/sessions
│       ├── services.py             # GET /api/services (static catalogue)
│       ├── activity.py             # GET /api/activity (paginated, filterable)
│       └── settings.py            # GET/PATCH /api/settings
│
├── gateway/
│   └── main.py                     # MCP aggregator — spawns institution subprocesses,
│                                   # namespaces their tools, routes calls
│
├── institutions/                   # One folder per connected institution
│   ├── uslugi/                     # uslugi.gov.mk — main government services portal
│   │   ├── main.py                 # FastMCP server, registers all uslugi tools
│   │   ├── config.py
│   │   ├── auth/                   # Browser-based login (Playwright), session storage
│   │   ├── client/                 # Authenticated HTTP client
│   │   └── tools/
│   │       ├── session_tools.py    # login, logout, check_session
│   │       ├── portal_tools.py     # info_passport_renewal (authenticated fetch)
│   │       ├── mvr_info.py         # 46 MVR public-info tools (no login needed)
│   │       └── fk_info.py          # 17 Pharmacists Chamber public-info tools
│   │
│   └── mojtermin/                  # mojtermin.mk — government appointment booking
│       ├── main.py                 # FastMCP server, registers all mojtermin tools
│       └── tools/
│           └── appointments.py     # get_locations, get_doctors, get_available_appointments …
│
├── agent/
│   └── gemini_agent.py             # Original CLI agent (still works standalone)
│
├── frontend/my-app/                # React application
│   └── src/
│       ├── api/                    # axios client + per-endpoint API modules
│       ├── contexts/AuthContext.js # JWT storage, login/logout
│       ├── hooks/useChat.js        # Chat state management
│       ├── components/
│       │   ├── layout/             # Sidebar, TopBar, ProtectedRoute, AppLayout
│       │   └── chat/               # MessageBubble, ChatInput, SuggestedQuestions
│       └── pages/
│           ├── SignIn.js           # Screen 1 — email + password
│           ├── Dashboard.js        # Screen 2 — quick actions, recent activity
│           ├── Assistant.js        # Screen 3 — chat interface
│           ├── Services.js         # Screen 4 — services catalogue by category
│           ├── Activity.js         # Screen 5 — paginated tool-call history
│           └── Settings.js         # Screen 6 — profile, language, notifications
│
├── storage/
│   └── app.db                      # SQLite database (auto-created, gitignored)
│
├── .env                            # Secrets — copy from .env.example
├── .env.example
└── requirements.txt
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A free [Google AI Studio](https://aistudio.google.com) API key
- Chromium/Google Chrome + matching ChromeDriver (required for Selenium-based institution tools, e.g. Agencija za Vrabotuvanje)

### 1. Clone and install Python dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

If you're running in Linux CI/server environments, also install a browser + driver for Selenium:

```bash
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set:

```env
GEMINI_API_KEY=your_key_here
JWT_SECRET=any_long_random_string
```

### 3. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

On startup the backend will:
- Create `storage/app.db` with all tables
- Spawn the gateway subprocess
- Connect to all institution MCP servers
- Print how many tools are available

### 4. Start the frontend

```bash
cd frontend/my-app
npm install
npm start
```

Open [http://localhost:3000](http://localhost:3000), register an account, and start chatting.

---

## How the AI Handles Conversations

1. The user sends a message via the React chat UI.
2. FastAPI passes it to `ChatService.chat()`, which holds the full conversation history per user.
3. The history + all tool schemas are sent to Gemini Flash.
4. Gemini decides which tool to call (if any) and returns a `function_call`.
5. The service calls the tool via the MCP gateway, which routes it to the right institution server.
6. The tool result is added to the history and sent back to Gemini.
7. Steps 4–6 repeat until Gemini produces a plain-text final answer.
8. The answer, the session, and an activity log entry are saved to the database.

---

## Adding a New Institution

### 1. Create the institution folder

```
institutions/
└── myinstitution/
    ├── __init__.py
    ├── main.py          ← FastMCP server
    └── tools/
        ├── __init__.py
        └── my_tools.py  ← your tool functions
```

### 2. Write your tools

```python
# institutions/myinstitution/tools/my_tools.py

def get_something(param: str) -> dict:
    """Description that Gemini will read to decide when to call this tool."""
    # Call your institution's API here
    return {"result": "..."}
```

Keep tool functions simple and synchronous. Return a plain dict or string. The gateway and ChatService handle all the MCP/async plumbing.

### 3. Register tools in main.py

```python
# institutions/myinstitution/main.py
from fastmcp import FastMCP
from institutions.myinstitution.tools.my_tools import get_something

mcp = FastMCP("myinstitution")

@mcp.tool()
def get_something_tool(param: str) -> dict:
    """Description Gemini will use."""
    return get_something(param)

if __name__ == "__main__":
    mcp.run()
```

### 4. Register the institution in the gateway

Open [`gateway/main.py`](gateway/main.py) and add your institution to the `INSTITUTIONS` list:

```python
INSTITUTIONS = [
    {"name": "uslugi.gov.mk",    "key": "uslugi",        "module": "institutions.uslugi.main"},
    {"name": "mojtermin.mk",     "key": "mojtermin",     "module": "institutions.mojtermin.main"},
    {"name": "myinstitution.mk", "key": "myinstitution", "module": "institutions.myinstitution.main"},  # ← add this
]
```

The `key` becomes the tool name prefix (e.g. `myinstitution__get_something`).

### 5. Update the services catalogue (optional)

Open [`backend/routers/services.py`](backend/routers/services.py) and add your institution's tools to the catalogue so they appear on the Services page in the UI.

That's all. Restart the backend — the gateway will pick up the new institution automatically.

---

## Adding Tools to an Existing Institution

For **uslugi.gov.mk**, add a new file under `institutions/uslugi/tools/` and import it in `institutions/uslugi/main.py`.

**Public-info tools** (no login needed) follow the pattern in [`mvr_info.py`](institutions/uslugi/tools/mvr_info.py):

```python
def _build_info(service_id: int) -> dict:
    import requests
    resp = requests.post(
        "https://uslugi.gov.mk/api/Services/GetServiceDetails",
        json={"serviceId": service_id},
        timeout=15,
    )
    return resp.json()

def mvr_info_my_new_service() -> dict:
    """What documents are needed for my new service."""
    return _build_info(9999)  # replace with real service ID
```

**Authenticated tools** (require login) follow the pattern in [`portal_tools.py`](institutions/uslugi/tools/portal_tools.py) — use the shared `authenticated_client` which injects the stored session cookies automatically.

Then register in `institutions/uslugi/main.py`:

```python
from institutions.uslugi.tools.my_new_file import mvr_info_my_new_service

@mcp.tool()
def mvr_info_my_new_service_tool() -> dict:
    """What documents are needed for my new service."""
    return mvr_info_my_new_service()
```

---

## Security Model

| Concern | How it is handled |
|---|---|
| User passwords | Hashed with bcrypt before storage, never stored in plaintext |
| Session tokens | JWT signed with `JWT_SECRET`, stored in browser localStorage |
| Portal credentials | User types them in a Playwright browser window — never seen by the AI or stored |
| Portal cookies | Fernet-encrypted before writing to disk |
| AI tool results | Tools return structured dicts only — raw cookies and tokens are never forwarded to Gemini |
| Protected routes | All `/api/*` endpoints (except auth) require a valid JWT |

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI model | Google Gemini 2.5 Flash (free tier) |
| Tool protocol | Model Context Protocol (MCP) over stdio |
| Backend | FastAPI + SQLAlchemy + SQLite |
| Auth | JWT (python-jose) + bcrypt |
| Frontend | React + React Router v6 + Tailwind CSS v3 |
| HTTP client | axios with JWT interceptor |
| Browser automation | Playwright (Chromium) |
