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
button.sample{background:#1e2530;color:#cbd5e1;padding:7px 12px;font-weight:500;font-size:13px}
button.sample:hover{background:#2a3342}
img{max-width:100%;border-radius:8px;border:1px solid #1e2530}
pre{white-space:pre-wrap;background:#0b0e14;padding:12px;border-radius:8px;overflow:auto;font-size:13px}
.flag{color:#fca5a5}.muted{color:#8b96a8}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:760px){.grid{grid-template-columns:1fr}}
.hit{animation:flash 1s}@keyframes flash{from{background:#7f1d1d}to{background:transparent}}
.tabs{display:flex;gap:6px;margin-bottom:12px;border-bottom:1px solid #1e2530}
.tab{background:none;color:#8b96a8;padding:8px 14px;border-radius:8px 8px 0 0;font-size:14px}
.tab.active{color:#fff;background:#1e2530}
.emailframe{width:100%;height:340px;border:1px solid #1e2530;border-radius:8px;background:#fff}
.badge{display:inline-block;padding:4px 12px;border-radius:8px;font-weight:700;font-size:13px;color:#fff}
.rl-critical{background:#dc2626}.rl-high{background:#ea580c}.rl-medium{background:#ca8a04}.rl-low{background:#16a34a}
.timeline{list-style:none;margin:0;padding:0}
.timeline li{position:relative;padding:0 0 18px 30px;border-left:2px solid #2a3342;margin-left:8px}
.timeline li:last-child{border-left-color:transparent}
.timeline .dot{position:absolute;left:-11px;top:0;font-size:16px}
.timeline .t-label{font-weight:600}.timeline .t-detail{color:#8b96a8;font-size:13px;word-break:break-all}
.timeline .t-ts{color:#5b6577;font-size:12px}
.mappin{width:100%;height:220px;border:0;border-radius:8px;margin-top:10px}
</style></head><body>
<header><h1>🎣 PhishTrap</h1><span class=muted>agentic phishing sandbox &amp; canary tracker</span></header>
<div class=wrap>"""

_FOOT = "</div></body></html>"


def chip(status: str) -> str:
    return f'<span class=chip style="background:{STATUS_COLORS.get(status,"#555")}">{e(status)}</span>'


def render_index(cases: list[dict], samples: list[dict] | None = None) -> str:
    import json as _json
    samples = samples or []
    sample_btns = "".join(
        f"<button type=button class=sample data-i={i}>📧 {e(s['name'])}</button>" for i, s in enumerate(samples)
    )
    samples_json = _json.dumps([s["content"] for s in samples])
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
        <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <button type=submit>Analyze &amp; trap</button>
          <span class=muted style="margin-left:6px">or load a sample:</span>
          {sample_btns}
        </div>
        <p class=muted style="margin-top:8px;font-size:13px">Tip: start the fake site with
          <code>python demo/fake_phish_site.py</code> so the sample links resolve.</p>
      </form>
    </div>
    <div class=card id=preview hidden>
      <div class=tabs>
        <button type=button class="tab active" data-t=rendered>📨 Rendered</button>
        <button type=button class="tab" data-t=source>&lt;/&gt; Source (.eml)</button>
      </div>
      <table id=pmeta style="margin:0 0 10px"></table>
      <div class=pane data-p=rendered>
        <iframe class=emailframe sandbox id=pframe></iframe>
        <p class=muted style="font-size:12px;margin-top:6px">Sandboxed preview — scripts &amp; navigation disabled.</p>
      </div>
      <div class=pane data-p=source hidden><pre id=psrc></pre></div>
      <div id=pflags style="margin-top:10px"></div>
    </div>
    <table><thead><tr><th>Case</th><th>Status</th><th>Subject</th><th>Sender</th><th>Brand</th><th>Hits</th></tr></thead>
    <tbody id=rows>{rows}</tbody></table>
    <script>
    const SAMPLES={samples_json};
    const esc=s=>(s||'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
    async function updatePreview(){{
      const raw=f.raw_email.value.trim();
      const box=document.getElementById('preview');
      if(!raw){{box.hidden=true;return;}}
      const fd=new FormData();fd.append('raw_email',raw);
      const j=await (await fetch('/preview',{{method:'POST',body:fd}})).json();
      box.hidden=false;
      const row=(k,v)=>v?`<tr><td class=muted style='width:120px'>${{k}}</td><td>${{esc(v)}}</td></tr>`:'';
      document.getElementById('pmeta').innerHTML=
        row('From',j.from)+row('Reply-To',j.reply_to)+row('Return-Path',j.return_path)+row('Subject',j.subject);
      const body=j.html||('<pre style=\"font:14px/1.5 system-ui;white-space:pre-wrap;padding:16px\">'+esc(j.text||'(empty)')+'</pre>');
      document.getElementById('pframe').srcdoc=
        '<!doctype html><meta charset=utf-8><base target=_blank><style>body{{margin:0;background:#fff;color:#111}}</style>'+body;
      document.getElementById('psrc').textContent=j.raw||'';
      document.getElementById('pflags').innerHTML=
        (j.flags&&j.flags.length)?'<b class=flag>Red flags:</b><ul>'+j.flags.map(x=>'<li class=flag>'+esc(x)+'</li>').join('')+'</ul>':'';
    }}
    document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{{
      document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===t));
      document.querySelectorAll('#preview .pane').forEach(p=>p.hidden=p.dataset.p!==t.dataset.t);
    }});
    document.querySelectorAll('.sample').forEach(b=>b.onclick=()=>{{
      f.raw_email.value=SAMPLES[+b.dataset.i]; updatePreview();
    }});
    let tmr; f.raw_email.oninput=()=>{{clearTimeout(tmr);tmr=setTimeout(updatePreview,400);}};
    f.onsubmit=async ev=>{{ev.preventDefault();
      const r=await fetch('/cases',{{method:'POST',body:new FormData(f)}});
      const j=await r.json(); location.href='/cases/'+j.id;}};
    new EventSource('/events').addEventListener('case',()=>setTimeout(()=>location.reload(),600));
    </script>""" + _FOOT


def _geo_str(h: dict) -> str:
    g = h.get("geo") or {}
    parts = [g.get("flag", ""), g.get("city", ""), g.get("country", "")]
    return e(" ".join(p for p in parts if p).strip()) or "<span class=muted>—</span>"


def _map_iframe(hits: list[dict]) -> str:
    for h in hits:
        g = h.get("geo") or {}
        if g.get("lat") is not None and g.get("lon") is not None:
            lat, lon = g["lat"], g["lon"]
            d = 4  # bbox half-size in degrees
            bbox = f"{lon-d},{lat-d},{lon+d},{lat+d}"
            src = (f"https://www.openstreetmap.org/export/embed.html?bbox={bbox}"
                   f"&marker={lat},{lon}&layer=mapnik")
            return f"<iframe class=mappin src='{e(src)}' loading=lazy></iframe>"
    return ""


def render_case(c: dict, abuse: str) -> str:
    from . import report
    v = c.get("verdict") or {}
    sb = c.get("sandbox") or {}
    email = c.get("email") or {}
    score, level = report.risk_score(c)
    ioc_rows = "".join(
        f"<tr><td class=muted>{e(i['type'])}</td><td>{e(i['value'])}</td></tr>" for i in c.get("iocs", [])
    ) or "<tr><td colspan=2 class=muted>none</td></tr>"
    hit_rows = "".join(
        f"<tr class=hit><td>{e(h['ts'])}</td><td>{e(h['ip'] or '')}</td>"
        f"<td>{_geo_str(h)}</td><td class=muted>{e((h['ua'] or '')[:40])}</td></tr>"
        for h in c.get("hits", [])
    ) or "<tr><td colspan=4 class=muted>No canary hits yet. Trigger the planted link to see one appear.</td></tr>"
    def _tl(ev: dict) -> str:
        detail = f"<div class=t-detail>{e(ev['detail'])}</div>" if ev.get("detail") else ""
        ts = f"<div class=t-ts>{e(ev['ts'])}</div>" if ev.get("ts") else ""
        return (f"<li><span class=dot>{ev['icon']}</span>"
                f"<div class=t-label>{e(ev['label'])}</div>{detail}{ts}</li>")
    timeline_items = "".join(_tl(ev) for ev in report.build_timeline(c))
    map_html = _map_iframe(c.get("hits", []))
    flags = "".join(f"<li class=flag>{e(fl)}</li>" for fl in email.get("flags", []))
    canaries = "".join(
        f"<li><code>{e(cn['url'])}</code> — decoy identity <b>{e(cn['persona']['full_name'])}</b> / "
        f"{e(cn['persona']['email'])}</li>" for cn in c.get("canaries", [])
    ) or "<li class=muted>No canary planted (page was not a credential phish).</li>"
    conf = v.get("confidence")
    shot = f"<img src='/shots/{e(c['screenshot'])}'>" if c.get("screenshot") else "<span class=muted>no screenshot</span>"

    return _HEAD + f"""
    <p><a href='/'>&larr; all cases</a></p>
    <h2>Case #{c['id']} {chip(c['status'])}
      <span class="badge rl-{level}" title="Risk score">RISK {score} · {level.upper()}</span></h2>
    <div class=card><h3>Timeline</h3><ul class=timeline>{timeline_items}</ul></div>
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
      <table id=hits><thead><tr><th>When</th><th>IP</th><th>Location</th><th>User-Agent</th></tr></thead>
        <tbody>{hit_rows}</tbody></table>
      {map_html}
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
