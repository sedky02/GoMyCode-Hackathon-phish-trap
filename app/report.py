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
