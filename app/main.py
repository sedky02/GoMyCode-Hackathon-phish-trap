import asyncio

from fastapi import FastAPI, Form, Request, UploadFile
from fastapi.responses import (FileResponse, HTMLResponse, JSONResponse,
                               PlainTextResponse, StreamingResponse)

from . import db, events, ingest, jobs, report
from .config import SHOTS_DIR
from .templates import render_case, render_index

app = FastAPI(title="PhishTrap")


@app.get("/", response_class=HTMLResponse)
def index():
    return render_index(db.list_cases())


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
    hit = db.record_hit(
        token, case_id,
        ip=request.client.host if request.client else "?",
        ua=request.headers.get("user-agent", ""),
        headers=dict(request.headers),
    )
    events.publish("hit", hit)
    # Benign 1x1 response; never reveal it's a trap.
    return PlainTextResponse("ok")
