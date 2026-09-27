"""Decide whether the sandboxed page is a credential-harvesting phish and map
its form fields to roles. One Claude vision call, with a heuristic pre-pass and
a heuristic fallback so the pipeline never hard-stops without an API key."""
import base64
import json
import os
from pathlib import Path

from .config import CLAUDE_MODEL

VERDICT_SCHEMA = {
    "type": "object",
    "properties": {
        "is_credential_phish": {"type": "boolean"},
        "impersonated_brand": {"type": "string"},
        "confidence": {"type": "number"},
        "reasoning": {"type": "string"},
        "field_map": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "role": {"type": "string",
                             "description": "one of: email, username, password, pin, otp, phone, name, recovery, website, other"},
                },
                "required": ["selector", "role"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["is_credential_phish", "impersonated_brand", "confidence", "reasoning", "field_map"],
    "additionalProperties": False,
}

# Order matters: most specific / sensitive hints first, so e.g. "recovery_email"
# matches "recover" before the generic "email".
_ROLE_HINTS = {
    "password": "password", "pass": "password", "pwd": "password",
    "recover": "recovery", "card": "card", "cvv": "card", "cvc": "card",
    "ssn": "card", "iban": "card", "otp": "otp", "pin": "pin",
    "email": "email", "e-mail": "email", "user": "username", "login": "username",
    "phone": "phone", "tel": "phone", "code": "otp",
    "name": "name",
}

# Field roles that, on their own, signal a data-harvesting form.
SENSITIVE_ROLES = {"password", "card", "otp", "pin", "recovery"}


def _role_for(field: dict) -> str:
    hay = " ".join(str(field.get(k, "")) for k in ("name", "id", "placeholder", "label", "autocomplete")).lower()
    if field.get("type") == "password":
        return "password"
    # Name/label hints win over the raw input type so e.g. a recovery-email
    # field (type=email) is treated as recovery, not a plain login email.
    for hint, role in _ROLE_HINTS.items():
        if hint in hay:
            return role
    if field.get("type") == "email":
        return "email"
    return "other"


def _heuristic(forms: list[dict]) -> dict:
    fields = [f for form in forms for f in form["fields"]]
    field_map = [{"selector": f["selector"], "role": _role_for(f)} for f in fields]
    roles = {m["role"] for m in field_map}
    sensitive = roles & SENSITIVE_ROLES
    # email + a couple of identity fields on one form is also a harvest form.
    identity_combo = "email" in roles and len(roles & {"name", "phone", "username"}) >= 1 and len(fields) >= 3
    is_phish = bool(sensitive) or identity_combo
    if sensitive:
        reason = f"Heuristic: sensitive field(s) present ({', '.join(sorted(sensitive))})."
        conf = 0.65
    elif identity_combo:
        reason = "Heuristic: form collects email plus multiple identity fields."
        conf = 0.6
    else:
        reason = "Heuristic: no credential/sensitive field detected."
        conf = 0.1
    return {
        "is_credential_phish": is_phish,
        "impersonated_brand": "unknown",
        "confidence": conf,
        "reasoning": reason,
        "field_map": field_map,
    }


def analyze(screenshot_path: str, forms: list[dict], email: dict) -> dict:
    heur = _heuristic(forms)
    # No forms at all -> nothing to submit, skip the API call.
    if not forms or not os.getenv("ANTHROPIC_API_KEY"):
        return heur
    try:
        import anthropic

        img = base64.standard_b64encode(Path(screenshot_path).read_bytes()).decode()
        prompt = (
            "You are a phishing-triage analyst inspecting a page opened in a sandbox after a user "
            "reported a suspicious email. Decide if this page harvests credentials or sensitive data. "
            "For every input field listed, assign a role so a decoy identity can be typed in.\n\n"
            f"Reported email subject: {email.get('subject')!r}\n"
            f"Sender: {email.get('from')!r}\n"
            f"Forms (JSON): {json.dumps(forms)[:6000]}\n\n"
            "Roles must be one of: email, username, password, pin, otp, phone, name, recovery, website, other. "
            "Reuse the exact selector strings from the form JSON."
        )
        client = anthropic.Anthropic()
        resp = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=2000,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": img}},
                {"type": "text", "text": prompt},
            ]}],
            output_config={"format": {"type": "json_schema", "schema": VERDICT_SCHEMA}},
        )
        if resp.stop_reason == "refusal":
            return heur
        text = next(b.text for b in resp.content if b.type == "text")
        verdict = json.loads(text)
        verdict["source"] = "claude"
        # Backfill any selectors the model omitted, using heuristics.
        seen = {m["selector"] for m in verdict["field_map"]}
        verdict["field_map"] += [m for m in heur["field_map"] if m["selector"] not in seen]
        return verdict
    except Exception as e:
        heur["reasoning"] += f" (Claude call failed: {type(e).__name__}: {e})"
        return heur
