# MCP Platform for Government Digital Services

A full-stack web application that lets Macedonian citizens interact with government online portals through a conversational AI assistant. Built with FastAPI, React, and the Model Context Protocol (MCP).

**Live:** http://89.168.115.57

---

## What It Does

Users log in to the web app, then chat with an AI assistant (powered by Google Gemini Flash or OpenAI GPT) that can look up information and take actions on government portals on their behalf — passport renewal info, doctor appointments, job listings, property certificates, company registration, and more.

The AI has no direct access to the portals. Instead, it calls **MCP tools** — structured functions that talk to each institution's API — and summarises the results in plain language.

---

## Supported Institutions

| Institution | What it covers |
|---|---|
| **uslugi.gov.mk** | Passports, ID cards, driver's licenses, administrative procedures |
| **mojtermin.mk** | Doctor appointments, available slots, medical specialties |
| **crm.com.mk** | Company registration, founders, annual reports |
| **mon.gov.mk** | Competitions, scholarships, educational services |
| **katastar.gov.mk** | Property certificates, parcels, buildings |
| **av.gov.mk** | Job listings, CV management, job applications |

---

## Architecture

```
[Internet]
     │
[nginx proxy :80/:443]
     │              │
[frontend :80]  [backend :8000]
                    │  stdio
                [Gateway]
                    │  SSE (Docker) / stdio (local)
    ┌──────┬─────────┼──────────┬──────┬──────────┐
    ▼      ▼         ▼          ▼      ▼          ▼
 uslugi mojtermin katastar    crm    mon       agencija
 :8001   :8002     :8003      :8004  :8005      :8006
```

Each institution runs as a **FastMCP** server. The gateway connects to all of them and exposes their tools under a namespaced format: `institutionname__toolname` (e.g. `mojtermin__get_doctors`, `crm__search_companies`).

---

## Folder Structure

```
MCP-Platform-for-Government-Digital-Services/
│
├── backend/                        # FastAPI application
│   ├── main.py                     # App entry point, lifespan, CORS
│   ├── config.py                   # Settings from .env
│   ├── models/                     # SQLAlchemy models (User, Chat, Activity)
│   ├── services/
│   │   ├── auth_service.py         # bcrypt + JWT
│   │   ├── chat_service.py         # ChatService — owns gateway subprocess
│   │   └── email_service.py        # Password reset emails (Gmail SMTP)
│   └── routers/
│       ├── auth.py                 # register, login, forgot/reset password
│       ├── chat.py                 # send message, session history
│       ├── services.py             # institutions catalogue
│       ├── activity.py             # paginated tool-call log
│       └── settings.py            # user profile & preferences
│
├── gateway/
│   └── main.py                     # MCP aggregator — connects to all institutions,
│                                   # namespaces their tools, routes calls
│
├── institutions/                   # One folder per connected institution
│   ├── uslugi/                     # uslugi.gov.mk
│   ├── mojtermin/                  # mojtermin.mk
│   ├── katastar/                   # e-uslugi.katastar.gov.mk
│   ├── crm/                        # crm.com.mk
│   ├── mon/                        # mon.gov.mk
│   └── agencijaZaVrabotuvanje/     # e-rabota.av.gov.mk
│
├── frontend/my-app/                # React application
│   └── src/
│       ├── api/                    # axios client + per-endpoint modules
│       ├── contexts/AuthContext.js
│       ├── pages/
│       │   ├── SignIn.js / Register.js
│       │   ├── Dashboard.js        # quick actions, institutions, recent activity
│       │   ├── Assistant.js        # AI chat interface
│       │   ├── Services.js         # institutions catalogue
│       │   ├── Activity.js         # tool-call history
│       │   ├── Settings.js         # profile, language, notifications
│       │   ├── ForgotPassword.js
│       │   └── ResetPassword.js
│       └── components/
│
├── nginx/
│   ├── nginx.conf                  # Production (SSL)
│   ├── nginx.local.conf            # Local development (HTTP only)
│   └── frontend.conf               # React SPA catch-all
│
├── Dockerfile                      # Shared Python image (backend + all institutions)
├── Dockerfile.frontend             # Multi-stage Node → nginx
├── docker-compose.yml              # Production orchestration (9 services)
├── docker-compose.override.yml     # Local dev overrides (exposes ports, no SSL)
├── DEPLOYMENT.md                   # Hosting & Docker explained in Macedonian
├── .env.example
└── requirements.txt
```

---

## Quick Start (Local)

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Google AI Studio](https://aistudio.google.com) API key (free) or OpenAI API key

### 1. Install dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 2. Configure environment

```bash
cp .env.example .env
# Set GEMINI_API_KEY (or OPENAI_API_KEY) and JWT_SECRET
```

### 3. Start the backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 4. Start the frontend

```bash
cd frontend/my-app
npm install
npm start
```

Open [http://localhost:3000](http://localhost:3000), register an account, and start chatting.

---

## Docker (Local Testing)

```bash
docker compose up
```

The `docker-compose.override.yml` is picked up automatically and exposes:
- `http://localhost:3000` → frontend
- `http://localhost:8000/docs` → FastAPI Swagger UI
- `http://localhost:80` → nginx proxy

---

## Docker (Production Deploy)

```bash
# On the server
git clone https://github.com/mmmitev987/MCP-Platform-for-Government-Digital-Services /app
cd /app
cp .env.example .env && nano .env   # fill in API keys
docker compose build
docker compose up -d
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full hosting details.

---

## How the AI Handles Conversations

1. User sends a message via the React chat UI.
2. FastAPI passes it to `ChatService.chat()` with the full conversation history.
3. History + all 56 tool schemas are sent to Gemini / GPT.
4. The model decides which tool to call and returns a `function_call`.
5. The service calls the tool via the MCP gateway → routed to the right institution.
6. The tool result is added to history and sent back to the model.
7. Steps 4–6 repeat until the model produces a plain-text final answer.
8. The answer, session, and activity log entry are saved to SQLite.

---

## Adding a New Institution

1. Create `institutions/myinstitution/main.py` with a `FastMCP` server and `@mcp.tool()` decorated functions.
2. Add the institution to `gateway/config.yaml`.
3. Add a new service entry in `backend/routers/services.py`.
4. Add metadata (name, description, icon) in `frontend/my-app/src/pages/Services.js` and `Dashboard.js`.
5. Add a Docker service in `docker-compose.yml` with `MCP_TRANSPORT=sse` and the appropriate `MCP_PORT`.

---

## Security Model

| Concern | How it is handled |
|---|---|
| User passwords | Hashed with bcrypt, never stored in plaintext |
| Session tokens | JWT signed with `JWT_SECRET`, expires in 7 days |
| Portal credentials | Entered in a Playwright browser window — never seen by the AI |
| Portal cookies | Fernet-encrypted before writing to disk |
| AI tool results | Structured dicts only — raw cookies/tokens never forwarded to the model |
| Protected routes | All `/api/*` endpoints (except auth) require a valid JWT |
| HTTPS redirect | Enabled in production via `PRODUCTION=true` middleware |

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI model | Google Gemini 2.5 Flash / OpenAI GPT-4o-mini |
| Tool protocol | Model Context Protocol (MCP) — SSE in Docker, stdio locally |
| Backend | FastAPI + SQLAlchemy + SQLite |
| Auth | JWT (python-jose) + bcrypt + Gmail SMTP (password reset) |
| Frontend | React + React Router v6 + Tailwind CSS v3 |
| Browser automation | Playwright (Chromium) + Selenium |
| Containerisation | Docker + Docker Compose (9 services) |
| Hosting | Oracle Cloud Free Tier — VM.Standard.E5.Flex |
