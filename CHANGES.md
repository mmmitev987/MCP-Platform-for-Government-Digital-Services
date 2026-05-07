# GovMCP — Лог на имплементирани барања

Овој документ ги опишува сите функционални и нефункционални барања имплементирани во проектот, заедно со точните фајлови и промени за секое барање.

---

## НФБ-11 · Структурирани грешки при неуспех на алатки

**Барање:** Секоја функција (tool) мора да враќа убаво структурирана грешка при неуспех, за да може LLM агентот да го извести корисникот.

**Формат:**
```json
{ "error": true, "code": "network_error", "message": "Human-readable description" }
```

**Кодови за грешки:** `network_error`, `auth_required`, `not_found`, `parse_error`, `browser_error`, `unexpected_error`, `adapter_down`

**Променети фајлови:**
- `institutions/shared/errors.py` *(нов)* — заеднички helper `tool_error(code, message)`
- `institutions/uslugi/tools/discovery.py` — сите 4 функции обвиткани со try/except
- `institutions/uslugi/tools/session_tools.py` — `login`, `logout`, `check_session`
- `institutions/mojtermin/tools/appointments.py` — сите 6 функции
- `institutions/crm/client/browser.py` — `search_companies`, `get_company_details`, `get_founders_and_directors`, `get_annual_reports`
- `institutions/mon/tools/apply_tools.py` — HTTP 401/403 → `auth_required`, 404 → `not_found`
- `institutions/mon/tools/session_tools.py`
- `institutions/mon/tools/document_tools.py`

---

## НФБ-12 · Fault isolation меѓу MCP адаптери

**Барање:** Дефект или паѓање на еден MCP адаптер не смее да влијае на функционирањето на останатите адаптери.

**Имплементација:**
- `gateway/main.py` целосно преработен
- Секоја институција добива своја `InstitutionConnection` класа со независен `AsyncExitStack`
- `connect()` враќа `True/False`, никогаш не крева исклучок
- `call_tool()` → обид → reconnect со `_reconnect_lock` → retry → враќа `adapter_down` грешка
- `asyncio.gather(*tasks, return_exceptions=True)` за паралелно, изолирано стартување

**Променети фајлови:**
- `gateway/main.py` — целосно преработен

---

## НФБ-15 (доверливост) · Трајна историја на разговори

**Барање:** Chat историјата мора да биде зачувана трајно и да не се губи при рестарт на серверот.

**Имплементација:**
- Пораките се зачувуваат во SQLite (модели `ChatSession` / `Message`) веднаш по прием
- In-memory кеш (`_histories`) е индексиран по `session_id` (не `user_id`)
- При cache miss по рестарт: `_load_history(session_id, db)` ги чита пораките од DB, сортирани по `created_at`
- Нови сесии го пред-сеедуваат кешот со `self._histories[chat_session.id] = []`

**Променети фајлови:**
- `backend/services/chat_service.py` — `_load_history`, `_histories` клуч, pre-seed логика

---

## НФБ-14 · Јасни пораки кога надворешен портал е недостапен

**Барање:** Системот мора да прикажува јасна порака за грешка кога надворешниот портал е недостапен.

**Имплементација (две нивоа):**

**Ниво 1 — Агент:** Детектира кога tool враќа `{ "error": true }`, додава slug во `portal_errors` листата  
**Ниво 2 — UI:** Амбер ⚠ индикатор под AI bubble со конкретното ime на порталот

**Променети фајлови:**
- `backend/services/chat_service.py` — `portal_errors: list[str]`, `_agentic_loop` враќа tuple
- `backend/schemas/chat.py` — `ChatResponse.portal_errors: list[str] = []`
- `backend/routers/chat.py` — unpack на 3-tuple
- `frontend/my-app/src/hooks/useChat.js` — `portalErrors` во message state, `errorKey()` функција
- `frontend/my-app/src/components/chat/MessageBubble.js` — `PORTAL_NAMES` dict, amber warning
- `frontend/my-app/src/pages/Assistant.js` — `clearError`, red banner со dismiss копче
- `frontend/my-app/src/locales/en.json` / `mk.json` — `portalWarning_one/other`, `dismiss`, `retry`

---

## НФБ-15 (проширливост) · Нова институција без промена на агентот

**Барање:** Нова институција мора да може да се додаде со креирање на нов MCP адаптер и регистрирање кај Gateway-от, без промени во LLM агентот.

**Имплементација:**
- `gateway/config.yaml` доби полиња `description` и `tool_rules` за секоја институција
- `backend/services/chat_service.py` — `_build_system_prompt(connected_slugs)` чита од `config.yaml` при стартување
- Системскиот промпт ги вклучува само активните институции (чии алатки се успешно регистрирани)
- `mon` институцијата додадена во `gateway/config.yaml` (претходно беше имплементирана но не регистрирана)

**За додавање нова институција — само 2 чекори:**
1. Креирај `institutions/<slug>/` директориум со MCP server
2. Додај запис во `gateway/config.yaml`

**Променети фајлови:**
- `gateway/config.yaml` — `description` + `tool_rules` за сите 4 институции; додаден `mon`
- `backend/services/chat_service.py` — `_STATIC_PROMPT_PREFIX`, `_STATIC_PROMPT_SUFFIX`, `_build_system_prompt()`

---

## НФБ-16 · Прецизни описи на алатките за брза LLM селекција

**Барање:** Описите на функциите (tools) мора да бидат доволно прецизни за LLM-от да може да ја избере најсоодведната во најбрз можен рок.

**Образец на опис:**
- Прва реченица: кога да се повика (trigger condition)
- Предуслов: што мора да се повика прво
- Конкретни примери за аргументи (кирилица за uslugi/mojtermin)
- Што НЕ треба да се прави (disambiguација од слични алатки)
- Returns секција со `On error:` формат

**Променети фајлови:**
- `institutions/uslugi/main.py` — сите 7 алатки преработени
- `institutions/mojtermin/main.py` — сите 6 алатки преработени
- `institutions/crm/main.py` — сите 4 алатки преработени; `get_founders_and_directors` и `get_annual_reports` добија IMPORTANT предупредување за free tier
- `institutions/mon/main.py` — сите 7 алатки преработени; `check_session_mon` преместен пред `login_mon`

---

## НФБ-17 · Агентот не смее да измислува информации

**Барање:** Агентот не смее да измислува информации за услуги, документи или рокови. Секој одговор мора да биде заснован исклучиво на податоци добиени од алатките.

**Имплементација:** Нова секција `FACTUAL GROUNDING — NEVER FABRICATE` во системскиот промпт:
- Забрана за измислување такси, рокови, документи, услуги
- Забрана за пополнување на празнини со тренинг-податоци
- Обврска да се повика алатка пред секој конкретен одговор
- Ако поле е `null` → „не е достапно на порталот", не тивко да се изостави

**Променети фајлови:**
- `backend/services/chat_service.py` — секција `FACTUAL GROUNDING` во `_STATIC_PROMPT_SUFFIX`

---

## НФБ-18 · Конзистентни одговори за исти прашања

**Барање:** Системот мора да врати конзистентни одговори за исти прашања — два идентични прашања во различни сесии не смеат да дадат контрадикторни информации за иста услуга.

**Имплементација (две нивоа):**

**Ниво 1 — API параметри:**
```python
temperature=0,  # детерминистички излез
seed=0,         # идентичен prompt → идентичен одговор
```

**Ниво 2 — Системски промпт:** Нова секција `CONSISTENCY`:
- Пријави СИТЕ полиња вратени од алатката (без селективно испуштање)
- Користи ТОЧНИ вредности (не заокружувај, не перифразирај)
- Фиксна структура по тип: услуга → документи → такси → рок → линк
- Ако поле е `null` → пишува „не е наведено", не тивко го изоставува
- Без додатни квалификации од општо знаење

**Променети фајлови:**
- `backend/services/chat_service.py` — `temperature=0`, `seed=0` во API повикот; секција `CONSISTENCY`

---

## НФБ-19 · Идентификација на намерата пред повик на алатка

**Барање:** Агентот мора да ја идентификува точната цел на корисникот пред да повика која било алатка. Ако барањето е нејасно, агентот мора да побара појаснување наместо да претпостави.

**Имплементација:** Нова секција `INTENT CLARIFICATION — ASK BEFORE YOU ACT` (прва секција во промптот):

**Кога е нејасно (мора да праша):**
- `"пасош"` → прв пат? обнова? замена? само такса?
- Доктор без град → `get_doctors_by_city` нема аргумент
- Состанок без датум → `get_available_appointments_by_name` нема аргумент
- Фирма без наведена информација → кој detail tool?
- Образовен документ без тип

**Правила:**
- Само ЕДНО прашање по ред — најважното парче
- Конкретни опции (2–4) кога е можно
- Ниедна алатка не се повикува додека не пристигне одговор

**Променети фајлови:**
- `backend/services/chat_service.py` — секција `INTENT CLARIFICATION` на почеток на `_STATIC_PROMPT_SUFFIX`

---

## НФБ-20 · ФБ-37 · Поддршка за нови јазици без промена на бизнис логиката

**Барање:** Системот мора да поддржува додавање на нови јазици без промена на бизнис логиката. Поддржани: македонски и англиски.

**Имплементација:** Централен јазичен регистар `src/locales/index.js`:

```
src/locales/index.js   ← ЕДИНСТВЕНИОТ фајл кој се менува
      ↓
src/i18n.js            ← никогаш не се менува
src/pages/Settings.js  ← никогаш не се менува
```

**За додавање нов јазик (пр. Албански):**
1. Креирај `src/locales/sq.json`
2. Во `src/locales/index.js` додај `import sq` и `{ code: "sq", label: "Shqip", resources: sq }`

**Променети фајлови:**
- `frontend/my-app/src/locales/index.js` *(нов)* — `LANGUAGES` array, `DEFAULT_LANGUAGE`
- `frontend/my-app/src/i18n.js` — чита од `index.js`, динамично гради `resources`
- `frontend/my-app/src/pages/Settings.js` — `LANGUAGES` import наместо хардкодирана листа
- `backend/models/user.py` — коментарот `"en"|"mk"` заменет со `BCP-47 code; see frontend/src/locales/index.js`

---

## НФБ-21 · Агентот одговара на јазикот на корисникот

**Барање:** Агентот мора да одговори на истиот јазик на кој што му било поставено прашањето (доколку LLM-от го поддржува истиот јазик).

**Имплементација:** Нова секција `LANGUAGE — ALWAYS MATCH THE USER'S LANGUAGE` во `_STATIC_PROMPT_PREFIX`:
- Детектира јазик по секоја порака
- Важи за сите типови одговори: прашања, грешки, резултати од алатки
- Примери: МК → МК, EN → EN, SQ → SQ, SR → SR
- Fallback на EN со порака ако јазикот не е поддржан
- Забрана за мешање јазици во еден одговор

**Променети фајлови:**
- `backend/services/chat_service.py` — секција `LANGUAGE` во `_STATIC_PROMPT_PREFIX`

---

## НФБ-23 · Пораките за грешка во природен јазик

**Барање:** Пораките за грешка мора да бидат напишани на природен јазик.

**Имплементација (два слоја):**

**Слој 1 — Агент:** Секцијата `TOOL ERROR HANDLING` преработена:
- Конкретни примери на природни реченици за секој код
- `"network_error"` → *"The [portal] portal isn't reachable right now — it may be temporarily down."*
- `"auth_required"` → *"You'll need to log in first before I can look that up."*
- Експлицитна забрана: `error codes`, `HTTP status`, `tool`, `adapter`, `MCP`, `subprocess`, `exception`

**Слој 2 — Frontend (React UI):**

| Пред | По |
|------|----|
| `"The request timed out. Please try again."` | `"That took a bit longer than expected. Please try again."` |
| `"An unexpected server error occurred."` | `"Something went wrong on our end."` |
| `"Failed to get a response."` | `"We couldn't get a response."` |
| `"Серверот е привремено недостапен."` | `"Во моментов не можеме да го достигнеме серверот."` |
| `"Барањето истече."` | `"Одговорот одзеде малку подолго отколку што очекувавме."` |

**Променети фајлови:**
- `backend/services/chat_service.py` — секција `TOOL ERROR HANDLING` во `_STATIC_PROMPT_SUFFIX`
- `frontend/my-app/src/locales/en.json` — `assistant.errors.*`, `portalWarning_*`
- `frontend/my-app/src/locales/mk.json` — `assistant.errors.*`, `portalWarning_*`

---

## НФБ-24 · Responsive UI — адаптација по екран

**Барање:** Интерфејсот мора автоматски да се адаптира во зависност од екранот на корисникот.

**Breakpoint стратегија:**

| Breakpoint | Сајдбар | Padding | Табели |
|------------|---------|---------|--------|
| `< lg` (< 1024px) | Скриен, hamburger ☰ + drawer | `p-4` | overflow-x-auto |
| `sm` (640px+) | Скриен, drawer | `p-6` | некои колони видливи |
| `lg+` (1024px+) | Секогаш видлив | `p-8` | сите колони |

**`AppLayout.js`:**
- Мобилна top bar со hamburger ☰ и лого (`lg:hidden`)
- Backdrop overlay со blur при отворен drawer
- Sidebar wrapper со `transition-transform duration-300` (slide animation)
- `pt-12 lg:pt-0` на main за простор под мобилниот header

**`Sidebar.js`:**
- Прифаќа `onClose` prop
- Close ✕ копче во header (`lg:hidden`)
- `NavLink.onClick = onClose` — автоматски затвора при навигација

**Pages:**
- `Dashboard`, `Activity`, `Services`, `Settings` — `p-4 sm:p-6 lg:p-8`
- `Dashboard` grid — `grid-cols-1 sm:grid-cols-2 xl:grid-cols-4`
- `Dashboard` table — `overflow-x-auto`, `action` колона `hidden sm:table-cell`
- `Activity` table — `overflow-x-auto`, `action` `hidden sm:table-cell`, `description` `hidden md:table-cell`
- `Assistant` — `px-4 sm:px-6 py-4 sm:py-6`
- `ChatInput` — `p-3 sm:p-4`, `gap-2 sm:gap-3`

**Променети фајлови:**
- `frontend/my-app/src/components/layout/AppLayout.js`
- `frontend/my-app/src/components/layout/Sidebar.js`
- `frontend/my-app/src/pages/Dashboard.js`
- `frontend/my-app/src/pages/Activity.js`
- `frontend/my-app/src/pages/Services.js`
- `frontend/my-app/src/pages/Settings.js`
- `frontend/my-app/src/pages/Assistant.js`
- `frontend/my-app/src/components/chat/ChatInput.js`

---

## Статус на сите барања

### Функционални барања

| ID | Опис | Статус |
|----|------|--------|
| ФБ-37 | Поддршка за повеќе јазици (македонски, англиски) |  НФБ-20 |

### Нефункционални барања — Безбедност

| ID | Опис | Статус |
|----|------|--------|
| НФБ-01 | Лозинките мора да бидат хаширани пред зачувување |  Постоечка имплементација |
| НФБ-02 | Сите комуникации мора да бидат шифрирани преку HTTPS | ⚠️ Делумно (локален dev, production config потребен) |
| НФБ-05 | Апликацијата мора да имплементира CSRF заштита |  Постоечка имплементација |

### Нефункционални барања — Перформанси

| ID | Опис | Статус |
|----|------|--------|
| НФБ-06 | Одговор на јавни прашања во рок од 9 секунди |  Постоечка имплементација |
| НФБ-07 | Без редундантни повици кон адаптери |  НФБ-16 (tool descriptions) |
| НФБ-08 | Поддршка за 10 истовремени корисници |  Постоечка имплементација (semaphore) |
| НФБ-09 | Претходен разговор се вчитува во рок од 6 секунди |  Постоечка имплементација |
| НФБ-10 | Историја на активности се вчитува во рок од 9 секунди |  Постоечка имплементација |

### Нефункционални барања — Доверливост

| ID | Опис | Статус |
|----|------|--------|
| НФБ-11 | Структурирана грешка при неуспех на tool |  Имплементирано |
| НФБ-12 | Паѓање на еден адаптер не влијае на останатите |  Имплементирано |
| НФБ-14 | Јасна порака кога надворешниот портал е недостапен |  Имплементирано |
| НФБ-15 | Chat историјата зачувана трајно |  Имплементирано |

### Нефункционални барања — Проширливост и точност

| ID | Опис | Статус |
|----|------|--------|
| НФБ-15 | Нова институција без промени во LLM агентот |  Имплементирано |
| НФБ-16 | Прецизни описи на алатките |  Имплементирано |
| НФБ-17 | Агентот не измислува информации |  Имплементирано |
| НФБ-18 | Конзистентни одговори за исти прашања |  Имплементирано |
| НФБ-19 | Идентификација на намерата пред повик на алатка |  Имплементирано |
| НФБ-20 | Нови јазици без промена на бизнис логиката |  Имплементирано |

### Нефункционални барања — Употребливост

| ID | Опис | Статус |
|----|------|--------|
| НФБ-21 | Агентот одговара на јазикот на корисникот |  Имплементирано |
| НФБ-23 | Пораки за грешка на природен јазик |  Имплементирано |
| НФБ-24 | Responsive UI |  Имплементирано |

---

## Преглед на сите променети фајлови

### Backend
| Фајл | Барање(а) |
|------|-----------|
| `backend/services/chat_service.py` | НФБ-15, НФБ-14, НФБ-15, НФБ-17, НФБ-18, НФБ-19, НФБ-21, НФБ-23 |
| `backend/schemas/chat.py` | НФБ-14 |
| `backend/routers/chat.py` | НФБ-14 |
| `backend/models/user.py` | НФБ-20 |

### Gateway
| Фајл | Барање(а) |
|------|-----------|
| `gateway/main.py` | НФБ-12 |
| `gateway/config.yaml` | НФБ-15 |

### Institutions
| Фајл | Барање(а) |
|------|-----------|
| `institutions/shared/errors.py` | НФБ-11 |
| `institutions/uslugi/main.py` | НФБ-16 |
| `institutions/uslugi/tools/discovery.py` | НФБ-11 |
| `institutions/uslugi/tools/session_tools.py` | НФБ-11 |
| `institutions/mojtermin/main.py` | НФБ-16 |
| `institutions/mojtermin/tools/appointments.py` | НФБ-11 |
| `institutions/crm/main.py` | НФБ-16 |
| `institutions/crm/client/browser.py` | НФБ-11 |
| `institutions/mon/main.py` | НФБ-16 |
| `institutions/mon/tools/apply_tools.py` | НФБ-11 |
| `institutions/mon/tools/session_tools.py` | НФБ-11 |
| `institutions/mon/tools/document_tools.py` | НФБ-11 |

### Frontend
| Фајл | Барање(а) |
|------|-----------|
| `frontend/my-app/src/locales/index.js` | НФБ-20, ФБ-37 |
| `frontend/my-app/src/i18n.js` | НФБ-20, ФБ-37 |
| `frontend/my-app/src/locales/en.json` | НФБ-14, НФБ-23 |
| `frontend/my-app/src/locales/mk.json` | НФБ-14, НФБ-23 |
| `frontend/my-app/src/hooks/useChat.js` | НФБ-14 |
| `frontend/my-app/src/components/chat/MessageBubble.js` | НФБ-14 |
| `frontend/my-app/src/components/chat/ChatInput.js` | НФБ-24 |
| `frontend/my-app/src/components/layout/AppLayout.js` | НФБ-24 |
| `frontend/my-app/src/components/layout/Sidebar.js` | НФБ-24 |
| `frontend/my-app/src/pages/Assistant.js` | НФБ-14, НФБ-24 |
| `frontend/my-app/src/pages/Dashboard.js` | НФБ-24 |
| `frontend/my-app/src/pages/Activity.js` | НФБ-24 |
| `frontend/my-app/src/pages/Services.js` | НФБ-24 |
| `frontend/my-app/src/pages/Settings.js` | НФБ-20, НФБ-24 |
