# 🎣 PhishTrap

Agentic phishing sandbox & canary tracker. Paste a suspected phishing email; an AI
agent safely opens the link in a sandboxed browser, recognizes the credential-harvesting
form, submits a **decoy identity laced with a canary token**, extracts IOCs, and alerts
you the moment the planted canary is ever touched.

> Defensive tool. It uses only fake data, submits **once** per case, and never attacks
> phishing infrastructure. Point it at sites you are authorized to investigate.

## Pipeline
```
email → ingest (headers/SPF/DKIM/links) → sandbox visit (screenshot + forms)
      → agent verdict (Claude vision + heuristics) → plant canary + submit fake data
      → IOCs + abuse report → 🚨 canary callback fires → live dashboard alert
```

## Run (4 commands)
```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
cp .env.example .env          # add ANTHROPIC_API_KEY (optional: heuristics work without it)
.venv/bin/uvicorn app.main:app --reload
```
Open http://localhost:8000

### Demo
```bash
.venv/bin/python demo/fake_phish_site.py     # terminal 2: the 'attacker' page on :9000
```
1. Paste `demo/samples/examplebank.eml` into the dashboard (its link points at the local fake site).
2. Watch status move `visiting → analyzing → trapped`; see the screenshot, verdict, and IOCs
   (including the harvested-credential POST endpoint). Terminal 2 logs the decoy credentials.
3. **The trap:** open the planted canary URL shown on the case page (from your phone/another
   browser) → a 🚨 hit with IP/UA/time appears live on the case.

To make the canary reachable by a *real* attacker, run `ngrok http 8000` and set
`CANARY_BASE_URL` in `.env` to the public https URL, then restart.

## Real isolation (optional)
```bash
docker build -f sandbox/Dockerfile -t phishtrap-sandbox .
# set SANDBOX_MODE=docker in .env
```
Runs each visit in a throwaway container (`--cap-drop ALL`, no host mounts beyond the
screenshot dir, `no-new-privileges`).

## Layout
- `app/ingest.py` — .eml parsing, header/auth red flags, URL extraction
- `sandbox/worker.py` / `submit.py` — Playwright visit & one-shot form submit
- `app/agent.py` — Claude vision verdict + field-role mapping (heuristic fallback)
- `app/canary.py` — decoy persona whose password/website *is* a canary callback URL
- `app/jobs.py` — orchestrates the per-case state machine
- `app/main.py` / `templates.py` — FastAPI, SSE dashboard, `/c/{token}` canary receiver
