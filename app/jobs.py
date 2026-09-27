import asyncio
import traceback

from . import agent, canary, db, events, report, sandbox
from .config import SHOTS_DIR, SUBMIT_THRESHOLD


def _set(case_id: int, status: str, **fields):
    db.update_case(case_id, status=status, **fields)
    events.publish("case", {"id": case_id, "status": status})


async def run_case(case_id: int, email: dict) -> None:
    """queued -> visiting -> analyzing -> trapped | benign | error."""
    try:
        target = email["links"][0]["href"] if email.get("links") else None
        if not target:
            _set(case_id, "benign", error="No URL found in email.")
            return
        db.update_case(case_id, target_url=target)

        _set(case_id, "visiting")
        shot = SHOTS_DIR / f"case_{case_id}.png"
        sb = await asyncio.to_thread(sandbox.visit, target, str(shot))
        if sb.get("error") and not sb.get("forms"):
            _set(case_id, "error", sandbox=sb, error=sb["error"])
            return
        db.update_case(case_id, final_url=sb.get("final_url"),
                       screenshot=shot.name if shot.exists() else None, sandbox=sb)

        _set(case_id, "analyzing")
        verdict = await asyncio.to_thread(agent.analyze, str(shot), sb.get("forms", []), email)
        db.update_case(case_id, verdict=verdict)

        submit_result = None
        if verdict["is_credential_phish"] and verdict["confidence"] >= SUBMIT_THRESHOLD:
            persona = canary.mint(case_id)
            fills = [
                {"selector": m["selector"], "value": canary.value_for_role(persona, m["role"])}
                for m in verdict["field_map"] if m["role"] != "other"
            ]
            plan = {"fills": fills, "submit_selector": _submit_selector(sb)}
            submit_result = await asyncio.to_thread(sandbox.submit, target, plan)
            db.update_case(case_id, submitted=1)

        iocs = report.collect_iocs(email, sb, submit_result)
        db.add_iocs(case_id, iocs)

        status = "trapped" if submit_result else "benign"
        _set(case_id, status)
    except Exception:
        _set(case_id, "error", error=traceback.format_exc()[-1000:])


def _submit_selector(sb: dict) -> str | None:
    for form in sb.get("forms", []):
        if form.get("submit_selector"):
            return form["submit_selector"]
    return None
