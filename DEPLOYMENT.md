# GovMCP — Хостирање и Докеризација

## Архитектура

Апликацијата е поделена на **9 Docker контејнери** кои комуницираат преку внатрешна мрежа (`mcp_net`):

| Контејнер | Улога |
|-----------|-------|
| `proxy` | nginx — прима барања од интернет, ги препраќа до backend и frontend |
| `frontend` | React апликација (статички build сервиран преку nginx) |
| `backend` | FastAPI сервер + Gateway кој ги поврзува сите институции |
| `uslugi` | MCP сервер за uslugi.gov.mk |
| `mojtermin` | MCP сервер за mojtermin.mk |
| `katastar` | MCP сервер за katastar.gov.mk |
| `crm` | MCP сервер за crm.com.mk |
| `mon` | MCP сервер за mon.gov.mk |
| `agencija` | MCP сервер за av.gov.mk |

```
[Интернет]
     │
[nginx proxy :80/:443]
     │              │
[frontend :80]  [backend :8000]
                    │
                [Gateway]
                    │ SSE
    ┌──────┬─────────┼──────────┬──────┬──────────┐
    ▼      ▼         ▼          ▼      ▼          ▼
 uslugi mojtermin katastar    crm    mon       agencija
 :8001   :8002     :8003      :8004  :8005      :8006
```

---

## Зошто микросервиси?

Секоја институција работи во **изолиран контејнер**. Ако една институција падне (пр. Катастар го смени API-то), останатите 5 продолжуваат да работат нормално.

Backend-от се поврзува со институциите преку **SSE (Server-Sent Events)** транспорт наместо stdio, бидејќи stdio не работи меѓу различни контејнери.

---

## Docker слики

Сите Python сервиси (backend + 6 институции) **делат една иста слика** (`govmcp-python:latest`) — се билдира еднаш, се стартува со различна команда преку `docker-compose.yml`.

Frontend има своја слика со **multi-stage build**:
1. **Фаза 1 (builder)** — Node.js го компајлира React кодот
2. **Фаза 2** — nginx го сервира финалниот build

```dockerfile
# Пример: Dockerfile.frontend
FROM node:20-alpine AS builder
RUN npm install --legacy-peer-deps
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
```

---

## Хостирање — Oracle Cloud Free Tier

Апликацијата е хостирана на **Oracle Cloud** на VM со:

| | |
|---|---|
| **Тип** | VM.Standard.E5.Flex (AMD) |
| **CPU / RAM** | 2 OCPU / 24 GB RAM |
| **OS** | Ubuntu 22.04 |
| **Јавна IP** | 89.168.115.57 |
| **Цена** | Always Free — не истекува |

Портовите **80** и **443** се отворени преку Oracle Security List (мрежен firewall). На самиот сервер, iptables е исто така конфигуриран да ги пропушта овие портови.

---

## Деплојмент процес

```bash
# 1. Клонирај го репото на серверот
git clone https://github.com/mmmitev987/MCP-Platform-for-Government-Digital-Services /app
cd /app

# 2. Постави ги environment variables
cp .env.example .env
nano .env   # пополни OPENAI_API_KEY, JWT_SECRET, SMTP итн.

# 3. Изгради ги сликите
docker compose build

# 4. Стартај ги сите контејнери
docker compose up -d

# 5. Следи ги логовите
docker compose logs backend -f
```

### Ажурирање на апликацијата

```bash
cd /app
git pull
docker compose build frontend   # или 'build' за сè
docker compose up -d
docker compose restart proxy
```

---

## Environment Variables (.env)

| Променлива | Опис |
|-----------|------|
| `OPENAI_API_KEY` | API клуч за OpenAI (или `GEMINI_API_KEY` за Gemini) |
| `LLM_PROVIDER` | `openai` или `gemini` |
| `JWT_SECRET` | Таен клуч за JWT токени |
| `SMTP_FROM_EMAIL` | Gmail адреса за испраќање мејлови |
| `SMTP_APP_PASSWORD` | Gmail App Password |
| `FRONTEND_URL` | Јавна URL на апликацијата (пр. `http://89.168.115.57`) |
| `PRODUCTION` | `true` во продукција |
