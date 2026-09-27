import asyncio

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import (FileResponse, HTMLResponse, JSONResponse,
                               PlainTextResponse, StreamingResponse)

from . import db, events, geo, ingest, jobs, report
from .config import ROOT, SHOTS_DIR
from .templates import render_case, render_index

app = FastAPI(title="PhishTrap")

SAMPLES_DIR = ROOT / "demo" / "samples"


def _load_samples() -> list[dict]:
    items = []
    for path in sorted(SAMPLES_DIR.glob("*.eml")):
        raw = path.read_text()
        subject = next((l[9:].strip() for l in raw.splitlines() if l.lower().startswith("subject:")), path.stem)
        items.append({"name": path.stem, "subject": subject, "content": raw})
    return items


@app.get("/samples")
def samples():
    return JSONResponse(_load_samples())


@app.get("/", response_class=HTMLResponse)
def index():
    return render_index(db.list_cases(), _load_samples())


@app.post("/preview")
async def preview(raw_email: str = Form("")):
    em = ingest.parse_email(raw_email.encode())
    return JSONResponse({
        "subject": em.get("subject"), "from": em.get("from"),
        "reply_to": em.get("reply_to"), "return_path": em.get("return_path"),
        "flags": em.get("flags", []), "links": em.get("links", []),
        "html": em.get("html"), "text": em.get("text"), "raw": em.get("raw"),
    })


@app.post("/cases")
async def create_case(raw_email: str = Form(""), eml: UploadFile | None = None):
    data = await eml.read() if eml is not None else raw_email.encode()
    email = ingest.parse_email(data)
    case_id = db.create_case(email["subject"], email.get("from", ""), email)
    events.publish("case", {"id": case_id, "status": "queued"})
    asyncio.create_task(jobs.run_case(case_id, email))
    return JSONResponse({"id": case_id})


@app.get("/cases/{case_id}", response_class=HTMLResponse)
def case_detail(case_id: int):
    case = db.get_case(case_id)
    if not case:
        return HTMLResponse("Not found", status_code=404)
    return render_case(case, report.abuse_report(case))


@app.get("/cases/{case_id}/iocs")
def case_iocs(case_id: int):
    case = db.get_case(case_id)
    if not case:
        return JSONResponse({"error": "not found"}, status_code=404)
    return JSONResponse({
        "case_id": case_id,
        "verdict": case.get("verdict"),
        "iocs": case.get("iocs"),
        "abuse_report": report.abuse_report(case),
    })


@app.get("/shots/{name}")
def shot(name: str):
    path = SHOTS_DIR / name
    return FileResponse(path) if path.exists() else PlainTextResponse("no image", 404)


@app.get("/events")
async def sse():
    return StreamingResponse(events.stream(), media_type="text/event-stream")


# --- Canary callback: the trap fires here -------------------------------------
@app.get("/c/{token}")
async def canary_hit(token: str, request: Request):
    rec = db.find_canary(token)
    case_id = rec["case_id"] if rec else None
    # Prefer X-Forwarded-For (real client behind a proxy / for demo IP spoofing).
    xff = request.headers.get("x-forwarded-for", "")
    ip = xff.split(",")[0].strip() if xff else (request.client.host if request.client else "?")
    headers = dict(request.headers)
    headers["_geo"] = geo.lookup(ip)
    hit = db.record_hit(token, case_id, ip=ip, ua=request.headers.get("user-agent", ""), headers=headers)
    hit["geo"] = headers["_geo"]
    events.publish("hit", hit)
    # Benign 1x1 response; never reveal it's a trap.
    return PlainTextResponse("ok")
