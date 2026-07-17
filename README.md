# Operator AI

An AI business employee. The owner sends natural-language requests over
WhatsApp; Groq turns each request into a structured execution plan; the
backend executes that plan through tool adapters (WhatsApp replies, invoice
PDF generation, email); progress is streamed live to a dashboard.

```
WhatsApp -> FastAPI webhook -> Planner (Groq) -> Plan (steps) -> Executor (tool adapters) -> Activity feed -> Dashboard (WebSocket)
```

## Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | Next.js 15 | Easy deployment on Vercel |
| Backend | FastAPI | Fast and simple |
| AI | Groq | Free, fast inference |
| Database | Supabase PostgreSQL | Hosted database with dashboard |
| File Storage | Supabase Storage | Store generated invoices |
| Email | Resend | Simple API and free tier |
| WhatsApp | Meta WhatsApp Cloud API | Official API |
| PDF | ReportLab | Pure Python, easy deployment |
| Hosting (Frontend) | Vercel | Best for Next.js |
| Hosting (Backend) | Railway | Simple FastAPI deployment |
| Secrets | Railway + Vercel environment variables | Easy management |

## Project structure

```
backend/            FastAPI service
  app/
    api/routes/      HTTP + WebSocket routes (whatsapp, planner, tasks, activity, ws)
    core/            config, DI wiring, WebSocket connection manager
    db/               async SQLAlchemy session
    llm/              PlannerLLM interface + Groq adapter
    models/           SQLAlchemy models (Task, Plan, PlanStep, ActivityEvent, WhatsAppMessage)
    schemas/          Pydantic request/response + plan schemas
    services/         planner, executor, orchestrator, activity, whatsapp, storage, email services
    tools/            ToolAdapter interface, registry, tool implementations
  alembic/            migrations
  Procfile            Railway start command
frontend/            Next.js 15 dashboard (App Router, Tailwind, shadcn/ui)
  src/
    app/page.tsx       dashboard: requests list + live activity timeline
    components/        UI components
    hooks/              WebSocket hook
    lib/                API client, types, config
```

Every integration (WhatsApp, the planner LLM, each tool) sits behind an
interface (`PlannerLLM`, `ToolAdapter`) so new tools or a different model can
be added without touching the planner/executor pipeline. See
`app/tools/setup.py` for the registered tools:

- `send_whatsapp_message` -- reply to the owner over WhatsApp
- `create_note` -- placeholder for a future notes/CRM integration
- `web_search` -- stub, not yet wired to a real provider
- `generate_invoice_pdf` -- renders a PDF with ReportLab, uploads it to
  Supabase Storage, returns a public URL
- `send_email` -- sends an email via Resend (e.g. to deliver an invoice link)

## Prerequisites / accounts you'll need

1. **Groq** -- API key from https://console.groq.com/keys (`GROQ_API_KEY`).
   Default model is `llama-3.3-70b-versatile`; override via `PLANNER_MODEL`.
2. **Supabase project** -- for both Postgres and Storage:
   - `DATABASE_URL`: Project Settings -> Database -> Connection string (URI).
     Use the pooled connection (port 6543) for Railway/serverless deploys.
   - `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY`: Project Settings -> API.
   - Create a Storage bucket (default name `invoices`, see
     `SUPABASE_STORAGE_BUCKET`) and mark it public, since generated invoice
     URLs are returned as public links. Use a private bucket + signed URLs
     instead if invoices shouldn't be publicly accessible.
3. **Email** -- pick one via `EMAIL_PROVIDER`:
   - `resend` (default) -- API key from https://resend.com/api-keys
     (`RESEND_API_KEY`). `RESEND_FROM_EMAIL` must be a verified sender/domain
     in Resend; the `onboarding@resend.dev` default only works for testing,
     sending to your own account email. Resend can't send from a
     `gmail.com`/other-provider address -- it requires DNS-verified domain
     ownership.
   - `gmail` -- no domain needed, sends from your real Gmail address via
     SMTP. Enable 2-Step Verification on the Google account, generate an App
     Password at https://myaccount.google.com/apppasswords, and set
     `GMAIL_ADDRESS` / `GMAIL_APP_PASSWORD`.
4. **Meta WhatsApp Business Cloud API** -- phone number ID + access token
   from a Meta developer app, plus a verify token you choose yourself
   (`WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN`,
   `WHATSAPP_VERIFY_TOKEN`).
5. **Railway** account (backend hosting) and **Vercel** account (frontend
   hosting), for deployment.

Also needed locally: Python 3.11+, Node.js 20+.

## Backend setup

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate        # .venv/bin/activate on macOS/Linux
pip install -r requirements.txt

cp .env.example .env          # fill in the values from "Prerequisites" above
alembic upgrade head

uvicorn app.main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`.

### Testing the pipeline without WhatsApp

`POST /planner/plan` with `{"owner_phone": "+1555...", "raw_request": "..."}`
creates a Task and runs the planner/executor pipeline exactly as a WhatsApp
message would. The dashboard's "Send a test request" form calls this
endpoint, so you can exercise the full flow (including invoice generation
and email) before WhatsApp is configured.

### WhatsApp webhook

Point your Meta app's webhook at `POST /webhook/whatsapp` (verification uses
`GET /webhook/whatsapp` with `WHATSAPP_VERIFY_TOKEN`). For local development,
tunnel port 8000 with ngrok or similar.

## Frontend setup

```bash
cd frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL / NEXT_PUBLIC_WS_URL
npm run dev
```

Open http://localhost:3000. The dashboard fetches `/tasks` and `/activity`
on load, then subscribes to `/ws/activity` for live updates as the backend
plans and executes each request.

## Deployment

### Backend on Railway

1. Create a new Railway project from this repo, setting the service's root
   directory to `backend/`. Railway's Nixpacks builder auto-detects Python
   from `requirements.txt` and uses `Procfile`'s `web:` line as the start
   command.
2. Add all the backend env vars from `.env.example` under the service's
   Variables tab (`DATABASE_URL`, `GROQ_API_KEY`, `SUPABASE_*`,
   `RESEND_*`, `WHATSAPP_*`, and set `CORS_ORIGINS` to your Vercel URL, e.g.
   `["https://your-app.vercel.app"]`).
3. Run migrations against the deployed database: either set Railway's
   "Pre-Deploy Command" (Settings -> Deploy) to `alembic upgrade head`, or
   run it manually with `railway run alembic upgrade head`.
4. Point the Meta WhatsApp webhook at your Railway URL
   (`https://<service>.up.railway.app/webhook/whatsapp`).

### Frontend on Vercel

1. Import this repo into Vercel and set the project's Root Directory to
   `frontend/` (Project Settings -> General -> Root Directory).
2. Add environment variables: `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL`
   pointing at the deployed Railway backend (`https://...railway.app` and
   `wss://...railway.app` respectively).
3. Deploy -- Vercel auto-detects Next.js, no build config needed.

## Adding a new tool

1. Implement `ToolAdapter` in `app/tools/` (`name`, `description`,
   `input_schema`, async `execute`).
2. Register it in `app/tools/setup.py::register_default_tools`.

The planner automatically sees it (tool specs are included in every LLM
prompt) and the executor can invoke it by name -- no other code changes
needed.
