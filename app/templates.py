from html import escape as e

STATUS_COLORS = {
    "queued": "#888", "visiting": "#3b82f6", "analyzing": "#a855f7",
    "trapped": "#ef4444", "benign": "#22c55e", "error": "#f59e0b",
}

_HEAD = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>PhishTrap</title><style>
:root{color-scheme:dark}
body{font:15px/1.5 system-ui,sans-serif;margin:0;background:#0b0e14;color:#e6e6e6}
a{color:#60a5fa;text-decoration:none}a:hover{text-decoration:underline}
header{padding:16px 24px;border-bottom:1px solid #1e2530;display:flex;align-items:center;gap:12px}
h1{font-size:18px;margin:0}.wrap{max-width:1100px;margin:0 auto;padding:24px}
.chip{display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600;color:#fff}
table{width:100%;border-collapse:collapse;margin-top:12px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #1e2530;font-size:14px}
th{color:#8b96a8;font-weight:600}
.card{background:#111621;border:1px solid #1e2530;border-radius:10px;padding:16px;margin:16px 0}
textarea{width:100%;box-sizing:border-box;min-height:120px;background:#0b0e14;color:#e6e6e6;
  border:1px solid #2a3342;border-radius:8px;padding:10px;font-family:ui-monospace,monospace;font-size:13px}
button{background:#2563eb;color:#fff;border:0;border-radius:8px;padding:10px 18px;font-weight:600;cursor:pointer}
img{max-width:100%;border-radius:8px;border:1px solid #1e2530}
pre{white-space:pre-wrap;background:#0b0e14;padding:12px;border-radius:8px;overflow:auto;font-size:13px}
.flag{color:#fca5a5}.muted{color:#8b96a8}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.grid{grid-template-columns:1fr}}
.hit{animation:flash 1s}@keyframes flash{from{background:#7f1d1d}to{background:transparent}}
</style></head><body>
<header><h1>🎣 PhishTrap</h1><span class=muted>agentic phishing sandbox &amp; canary tracker</span></header>
<div class=wrap>"""

_FOOT = "</div></body></html>"


def chip(status: str) -> str:
    return f'<span class=chip style="background:{STATUS_COLORS.get(status,"#555")}">{e(status)}</span>'


def render_index(cases: list[dict]) -> str:
    rows = "".join(
        f"<tr><td><a href='/cases/{c['id']}'>#{c['id']}</a></td>"
        f"<td>{chip(c['status'])}</td>"
        f"<td>{e(c['subject'] or '')[:60]}</td>"
        f"<td class=muted>{e(c['sender'] or '')}</td>"
        f"<td>{e(str(c['brand'] or ''))}</td>"
        f"<td>{'🚨 '+str(c['hit_count']) if c['hit_count'] else ''}</td></tr>"
        for c in cases
    ) or "<tr><td colspan=6 class=muted>No cases yet — submit an email below.</td></tr>"
    return _HEAD + f"""
    <div class=card>
      <form id=f>
        <label>Paste a suspicious email (raw .eml or just the body with a link):</label>
        <textarea name=raw_email placeholder="From: ...\nSubject: ...\n\nClick here: https://..."></textarea>
        <div style="margin-top:10px"><button type=submit>Analyze &amp; trap</button></div>
      </form>
    </div>
    <table><thead><tr><th>Case</th><th>Status</th><th>Subject</th><th>Sender</th><th>Brand</th><th>Hits</th></tr></thead>
    <tbody id=rows>{rows}</tbody></table>
    <script>
    f.onsubmit=async ev=>{{ev.preventDefault();
      const r=await fetch('/cases',{{method:'POST',body:new FormData(f)}});
      const j=await r.json(); location.href='/cases/'+j.id;}};
    new EventSource('/events').addEventListener('case',()=>setTimeout(()=>location.reload(),600));
    </script>""" + _FOOT


def render_case(c: dict, abuse: str) -> str:
    v = c.get("verdict") or {}
    sb = c.get("sandbox") or {}
    email = c.get("email") or {}
    ioc_rows = "".join(
        f"<tr><td class=muted>{e(i['type'])}</td><td>{e(i['value'])}</td></tr>" for i in c.get("iocs", [])
    ) or "<tr><td colspan=2 class=muted>none</td></tr>"
    hit_rows = "".join(
        f"<tr class=hit><td>{e(h['ts'])}</td><td>{e(h['ip'] or '')}</td><td class=muted>{e((h['ua'] or '')[:50])}</td></tr>"
        for h in c.get("hits", [])
    ) or "<tr><td colspan=3 class=muted>No canary hits yet. Trigger the planted link to see one appear.</td></tr>"
    flags = "".join(f"<li class=flag>{e(fl)}</li>" for fl in email.get("flags", []))
    canaries = "".join(
        f"<li><code>{e(cn['url'])}</code> — decoy identity <b>{e(cn['persona']['full_name'])}</b> / "
        f"{e(cn['persona']['email'])}</li>" for cn in c.get("canaries", [])
    ) or "<li class=muted>No canary planted (page was not a credential phish).</li>"
    conf = v.get("confidence")
    shot = f"<img src='/shots/{e(c['screenshot'])}'>" if c.get("screenshot") else "<span class=muted>no screenshot</span>"

    return _HEAD + f"""
    <p><a href='/'>&larr; all cases</a></p>
    <h2>Case #{c['id']} {chip(c['status'])}</h2>
    <div class=grid>
      <div class=card><h3>What the sandbox saw</h3>{shot}
        <p class=muted>Target: {e(c.get('target_url') or '')}<br>Final: {e(c.get('final_url') or '')}
        {('<br>IP: '+e(sb.get('ip'))) if sb.get('ip') else ''}</p></div>
      <div class=card><h3>Verdict</h3>
        <p><b>{'⚠️ Credential phishing' if v.get('is_credential_phish') else '✅ Not a credential phish'}</b>
        {f'&mdash; impersonating <b>{e(str(v.get("impersonated_brand")))}</b>' if v.get('impersonated_brand') else ''}
        {f'<br>confidence {conf:.0%}' if isinstance(conf,(int,float)) else ''}
        {f'<br><span class=muted>source: {e(v.get("source","heuristic"))}</span>' if v else ''}</p>
        <p>{e(str(v.get('reasoning','')))}</p>
        <h4>Email red flags</h4><ul>{flags or '<li class=muted>none</li>'}</ul></div>
    </div>
    <div class=card><h3>Planted canaries (the trap)</h3><ul>{canaries}</ul>
      <p class=muted>If the attacker ever opens the planted link or reuses the decoy password, a hit appears below.</p>
      <h3>🚨 Canary hits</h3>
      <table id=hits><thead><tr><th>When</th><th>IP</th><th>User-Agent</th></tr></thead><tbody>{hit_rows}</tbody></table>
    </div>
    <div class=grid>
      <div class=card><h3>Indicators of Compromise</h3>
        <table>{ioc_rows}</table>
        <p style=margin-top:10px><a href='/cases/{c['id']}/iocs'>Export JSON</a></p></div>
      <div class=card><h3>Abuse report (draft)</h3><pre>{e(abuse)}</pre></div>
    </div>
    <script>
    const es=new EventSource('/events');
    es.addEventListener('hit',ev=>{{if(JSON.parse(ev.data).case_id=={c['id']})location.reload();}});
    es.addEventListener('case',ev=>{{if(JSON.parse(ev.data).id=={c['id']})location.reload();}});
    </script>""" + _FOOT
