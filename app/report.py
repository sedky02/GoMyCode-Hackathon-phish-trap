from urllib.parse import urlparse

from .ingest import domain_of


def collect_iocs(email: dict, sandbox: dict, submit_result: dict | None) -> list[tuple[str, str]]:
    iocs: list[tuple[str, str]] = []
    for link in email.get("links", []):
        iocs.append(("url", link["href"]))
        iocs.append(("domain", domain_of(link["href"])))
    if email.get("from"):
        iocs.append(("sender", email["from"]))
    if email.get("reply_to"):
        iocs.append(("reply_to", email["reply_to"]))
    if sandbox.get("final_url"):
        iocs.append(("final_url", sandbox["final_url"]))
        iocs.append(("domain", domain_of(sandbox["final_url"])))
    if sandbox.get("ip"):
        iocs.append(("ip", sandbox["ip"]))
    for r in sandbox.get("redirects", []):
        iocs.append(("redirect", r))
    if submit_result:
        for post in submit_result.get("posted_to", []):
            iocs.append(("harvest_endpoint", post))
            iocs.append(("domain", domain_of(post)))
    # de-dup, drop empties
    return sorted({(t, v) for t, v in iocs if v})


def risk_score(case: dict) -> tuple[int, str]:
    """0-100 severity from red flags, verdict confidence, trap outcome and hits."""
    email = case.get("email") or {}
    v = case.get("verdict") or {}
    score = 0
    score += min(len(email.get("flags", [])) * 12, 40)          # up to 40 from email red flags
    if v.get("is_credential_phish"):
        score += int((v.get("confidence") or 0) * 35)            # up to 35 from verdict
    if case.get("submitted"):
        score += 10                                              # trap was planted
    if case.get("hits"):
        score += 15                                              # attacker actually called back
    score = min(score, 100)
    level = "critical" if score >= 75 else "high" if score >= 50 else "medium" if score >= 25 else "low"
    return score, level


def build_timeline(case: dict) -> list[dict]:
    """Chronological events reconstructed from what the case stored."""
    email = case.get("email") or {}
    sb = case.get("sandbox") or {}
    v = case.get("verdict") or {}
    events = [{"icon": "📧", "label": "Email reported", "detail": email.get("subject", ""),
               "ts": case.get("created_at", "")}]
    if case.get("screenshot") or sb.get("final_url"):
        events.append({"icon": "🌐", "label": "Opened in sandbox",
                       "detail": case.get("final_url") or case.get("target_url") or "", "ts": ""})
    if v:
        verdict = "Credential phishing" if v.get("is_credential_phish") else "Not a credential phish"
        events.append({"icon": "🧠", "label": f"Agent verdict: {verdict}",
                       "detail": f"{(v.get('confidence') or 0):.0%} confidence", "ts": ""})
    for cn in case.get("canaries", []):
        events.append({"icon": "🪤", "label": "Canary planted",
                       "detail": cn.get("url", ""), "ts": cn.get("created_at", "")})
    for h in reversed(case.get("hits", [])):
        g = h.get("geo") or {}
        loc = f"{g.get('flag','')} {g.get('city','')} {g.get('country','')}".strip()
        events.append({"icon": "🚨", "label": "Attacker callback",
                       "detail": f"{h.get('ip','')} · {loc}".strip(" ·"), "ts": h.get("ts", "")})
    return events


def abuse_report(case: dict) -> str:
    v = case.get("verdict") or {}
    iocs = case.get("iocs", [])
    doms = sorted({i["value"] for i in iocs if i["type"] == "domain"})
    endpoints = [i["value"] for i in iocs if i["type"] == "harvest_endpoint"]
    lines = [
        "Subject: Phishing site abuse report",
        "",
        "To whom it may concern,",
        "",
        f"The following site is impersonating {v.get('impersonated_brand', 'a brand')} to harvest "
        "user credentials, and was identified via a reported phishing email.",
        "",
        f"Landing / final URL: {case.get('final_url') or case.get('target_url')}",
        "Involved domains: " + (", ".join(doms) or "n/a"),
        "Credential POST endpoint(s): " + (", ".join(endpoints) or "n/a"),
        "",
        "Please investigate and take the site down. Full IOC list attached.",
    ]
    return "\n".join(lines)
