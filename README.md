# PhishTrap

Agentic phishing sandbox & canary tracker — turn a reported phishing email into
actionable threat intelligence, automatically.

> Defensive tool. It uses only fake data, submits **once** per case, and never attacks
> phishing infrastructure. Point it at sites you are authorized to investigate.

## The problem

When someone reports a suspicious email, triaging it is slow and manual. An analyst
has to open the link in an isolated VM by hand (or pay for a sandbox service) just to
see what the page does, then copy indicators around by hand. Worse, even after
confirming it's phishing, you're left with a dead end: you know *you* were targeted,
but you have no way to learn anything about the **attacker** behind it.

## The solution

PhishTrap automates the whole loop and adds an attribution layer on top:

1. **Ingest** — paste a raw `.eml` or an email body. It parses headers and flags
   red flags (SPF/DKIM/DMARC failures, Reply-To/Return-Path mismatches, deceptive
   link text) and extracts URLs.
2. **Detonate safely** — a headless browser opens the link in a sandbox, follows
   redirects, screenshots the page, and extracts every form and field.
3. **Agent verdict** — Claude (vision + structured output) decides whether the page
   harvests credentials, identifies the impersonated brand, and maps each form field
   to a role. A heuristic pre-pass/fallback means it works even with no API key.
4. **Plant the trap** — for a confirmed phish, it fills the form with a **decoy
   identity whose password/fields are a unique canary callback URL** and submits once.
   The form's POST endpoint (the attacker's harvesting backend) is captured as an IOC.
5. **Intel + attribution** — a per-case dashboard shows the rendered email, sandbox
   screenshot, verdict, risk score, timeline, and IOCs, plus a ready-to-send abuse
   report. **The moment the attacker reuses the planted canary, you get a live alert
   with their IP, geolocation (map pin), user-agent, and timestamp** — tied back to the
   exact email.

The individual pieces (URL sandboxes, canary tokens) exist separately; the value here
is the agent-driven glue that connects **email → verdict → planted canary → attacker
callback** in one console.

## Install & run locally

Requirements: Python 3.11+ and (optional) Docker for isolated sandbox mode.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
cp .env.example .env          # add ANTHROPIC_API_KEY (optional — heuristics work without it)
.venv/bin/uvicorn app.main:app --port 8000
```
Open http://localhost:8000

> Run **without** `--reload`. The dashboard holds a live SSE connection, and uvicorn's
> reloader deadlocks waiting for it to close. Restart manually after code changes.

### Demo

```bash
# terminal 2 — the stand-in "attacker" phishing site (routes: /login /o365 /verify /gift)
.venv/bin/python demo/fake_phish_site.py
```
1. On the dashboard, click a **sample** email (or paste one) → **Analyze & trap**.
2. Watch the status move `visiting → analyzing → trapped`. Open the case to see the
   rendered email, screenshot, verdict, risk score, timeline, and IOCs (including the
   harvested-credential POST endpoint). Terminal 2 logs the decoy credentials.
3. **Fire the canary:** copy the planted canary URL from the case page and open it —
   from your phone, or with a spoofed IP to demo geolocation:
   ```bash
   curl -H "X-Forwarded-For: 8.8.8.8" http://localhost:8000/c/<token>
   ```
   A callback row (IP, flag + city, user-agent, time) and a map pin appear **live** on
   the case, and its risk jumps to CRITICAL.

To let a *real* attacker reach the canary, run `ngrok http 8000`, set `CANARY_BASE_URL`
in `.env` to the public https URL, and restart.

### Configuration (`.env`)
| Var | Purpose |
|---|---|
| `ANTHROPIC_API_KEY` | Enables the Claude vision verdict (optional; heuristics otherwise) |
| `CLAUDE_MODEL` | Model id (default `claude-sonnet-5`) |
| `CANARY_BASE_URL` | Base URL woven into planted canary links (use the ngrok URL for real traps) |
| `SANDBOX_MODE` | `local` (default) or `docker` |
| `SUBMIT_THRESHOLD` | Min agent confidence before submitting decoy data (default `0.6`) |

### Isolated sandbox (optional)
```bash
docker build -f sandbox/Dockerfile -t phishtrap-sandbox .
# set SANDBOX_MODE=docker in .env
```
Each visit runs in a throwaway container (`--cap-drop ALL`, `no-new-privileges`, no host
mounts beyond the screenshot dir).

## Architecture

```
 Dashboard ──POST /cases──▶ ingest ──▶ job runner (asyncio)
 (SSE live)                 headers/    │
                            flags/URLs  ▼
                    ┌─────── sandbox (Playwright, local or Docker) ───────┐
                    │  worker.py: visit → redirects, screenshot, forms     │
                    │        │                          ▲ field map + data │
                    │        ▼                          │                  │
                    │  agent.py: Claude vision ──▶ canary.py: decoy +      │
                    │  verdict + field roles       unique callback URL     │
                    │  submit.py: fill + submit once → capture POST target │
                    └──────────────────────────────────────────────────────┘
                                        │ artifacts
                                        ▼
      canary server  ◀── GET /c/{token} ── SQLite (cases, iocs, canaries, hits)
      (records IP/geo/UA/time,             │
       pushes SSE alert)                   ▼
                                    Dashboard: email viewer, screenshot,
                                    verdict, risk, timeline, hits+map, IOCs,
                                    abuse report  ◀── report.py
```

**Request flow.** FastAPI ([app/main.py](app/main.py)) accepts a case and spawns an
async job ([app/jobs.py](app/jobs.py)) that walks the state machine
`queued → visiting → analyzing → trapped | benign | error`, emitting Server-Sent Events
so the dashboard updates live. Browser actions run out-of-process
([app/sandbox.py](app/sandbox.py) dispatches to [sandbox/worker.py](sandbox/worker.py) /
[sandbox/submit.py](sandbox/submit.py)) either as a local subprocess or a locked-down
Docker container. Everything persists in SQLite ([app/db.py](app/db.py)); screenshots
land on disk.

### Module map
| File | Responsibility |
|---|---|
| [app/main.py](app/main.py) | FastAPI app, routes, SSE, `/c/{token}` canary receiver |
| [app/ingest.py](app/ingest.py) | `.eml` parsing, auth/header red flags, URL extraction |
| [app/jobs.py](app/jobs.py) | Per-case async state machine |
| [app/sandbox.py](app/sandbox.py) | Dispatch browser actions to subprocess/Docker |
| [sandbox/worker.py](sandbox/worker.py) | Playwright visit: redirects, screenshot, forms |
| [sandbox/submit.py](sandbox/submit.py) | Fill decoy data and submit once; capture POST target |
| [app/agent.py](app/agent.py) | Claude vision verdict + field-role mapping (heuristic fallback) |
| [app/canary.py](app/canary.py) | Decoy persona whose data carries a unique canary URL |
| [app/geo.py](app/geo.py) | Best-effort IP geolocation for callbacks |
| [app/report.py](app/report.py) | IOC collection, risk score, timeline, abuse report |
| [app/db.py](app/db.py) | SQLite schema and access |
| [app/events.py](app/events.py) | Server-Sent Events pub/sub |
| [app/templates.py](app/templates.py) | Server-rendered dashboard UI |
| [demo/fake_phish_site.py](demo/fake_phish_site.py) | Stand-in attacker site for the demo |

### HTTP routes
| Route | Purpose |
|---|---|
| `GET /` | Dashboard (submit form, live case queue) |
| `POST /cases` | Ingest an email and start a case |
| `POST /preview` | Parse an email for the live rendered/source preview |
| `GET /cases/{id}` | Case detail (email viewer, verdict, timeline, hits, IOCs) |
| `GET /cases/{id}/iocs` | Export IOCs + abuse report as JSON |
| `GET /c/{token}` | **Canary callback** — records IP/geo/UA and fires a live alert |
| `GET /events` | Server-Sent Events stream for live updates |
| `GET /shots/{name}` | Sandbox screenshots |

### Tech stack
FastAPI · Playwright (Chromium) · Anthropic Claude (vision + structured output) ·
SQLite · Faker · server-rendered HTML + SSE.
