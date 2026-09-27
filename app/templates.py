from html import escape as e

# Status -> semantic pill class (tinted, not solid). Kept for reference/reuse.
STATUS_COLORS = {
    "queued": "#9aa4b2", "visiting": "#5b9bff", "analyzing": "#a78bfa",
    "trapped": "#f2555a", "benign": "#3fb950", "error": "#e0a23a",
}

ICONS = {
    "shield": '<path d="M12 3l7 3v5c0 4.5-3 7.6-7 9-4-1.4-7-4.5-7-9V6z"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3.5 7l8.5 6 8.5-6"/>',
    "globe": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/>'
             '<path d="M12 3c2.6 2.7 2.6 15.3 0 18M12 3c-2.6 2.7-2.6 15.3 0 18"/>',
    "cpu": '<rect x="7" y="7" width="10" height="10" rx="1.5"/>'
           '<path d="M10 7V4M14 7V4M10 20v-3M14 20v-3M7 10H4M7 14H4M20 10h-3M20 14h-3"/>',
    "target": '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3.2"/>',
    "alert": '<path d="M10.3 4.3l-7 12A1.5 1.5 0 004.6 19h14.8a1.5 1.5 0 001.3-2.3l-7-12a1.5 1.5 0 00-2.6 0z"/>'
             '<path d="M12 9v4"/><path d="M12 16.5h.01"/>',
    "download": '<path d="M12 4v10"/><path d="M8 11l4 4 4-4"/><path d="M5 19h14"/>',
    "external": '<path d="M14 5h5v5"/><path d="M19 5l-9 9"/><path d="M18 13.5V19H5V6h5.5"/>',
    "inbox": '<path d="M4 13l2.4-7A1 1 0 017.3 5h9.4a1 1 0 01.95.7L20 13"/>'
             '<path d="M4 13v5a1 1 0 001 1h14a1 1 0 001-1v-5h-5a3 3 0 01-6 0z"/>',
    "code": '<path d="M9 8l-4 4 4 4M15 8l4 4-4 4"/>',
    "eye": '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z"/><circle cx="12" cy="12" r="2.6"/>',
    "clock": '<circle cx="12" cy="12" r="8"/><path d="M12 8v4l3 2"/>',
}

# timeline emoji (from report.build_timeline) -> (icon name, node color class)
TL_MAP = {
    "📧": ("mail", "n-neutral"), "🌐": ("globe", "n-info"), "🧠": ("cpu", "n-violet"),
    "🪤": ("target", "n-warn"), "🚨": ("alert", "n-danger"),
}


def _icon(name: str, cls: str = "") -> str:
    return (f'<svg class="ico {cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">{ICONS.get(name, "")}</svg>')


_HEAD = """<!doctype html><html><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>PhishTrap</title><style>
:root{
  color-scheme:dark;
  --bg:#0a0c10; --surface:#11141b; --surface-2:#161a22; --raise:#1b2029;
  --border:#20252f; --border-2:#2a313d;
  --fg:#e7eaf0; --fg-2:#9aa4b2; --fg-3:#69727f;
  --accent:#4d7cfe; --accent-2:#3f6ae0; --accent-fg:#fff;
  --danger:#f2555a; --warn:#e0a23a; --success:#3fb950; --info:#5b9bff; --violet:#a78bfa;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  --r:8px; --r-sm:6px;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font:14px/1.55 -apple-system,"Segoe UI",Roboto,Inter,system-ui,sans-serif;
  -webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}a:hover{color:#6a91ff}
h1,h2,h3,h4{margin:0;font-weight:600;letter-spacing:-.01em}
.ico{width:16px;height:16px;flex:none;vertical-align:-3px}
.mono{font-family:var(--mono)}
.muted{color:var(--fg-2)}.subtle{color:var(--fg-3)}
code{font-family:var(--mono);font-size:.86em;background:var(--surface-2);
  border:1px solid var(--border);border-radius:4px;padding:1px 5px}

/* App bar */
.appbar{position:sticky;top:0;z-index:20;display:flex;align-items:center;gap:14px;
  height:56px;padding:0 24px;background:rgba(10,12,16,.85);backdrop-filter:blur(8px);
  border-bottom:1px solid var(--border)}
.brand{display:flex;align-items:center;gap:9px;font-weight:600;letter-spacing:-.02em}
.brand .mark{display:grid;place-items:center;width:28px;height:28px;border-radius:7px;
  background:linear-gradient(180deg,#20263300,#2a3242);border:1px solid var(--border-2);color:var(--accent)}
.brand .mark .ico{width:17px;height:17px}
.brand small{display:block;font-weight:400;font-size:11px;color:var(--fg-3);letter-spacing:0}
.appbar .spacer{flex:1}
.live{display:inline-flex;align-items:center;gap:7px;font-size:12px;color:var(--fg-2)}
.live .dot{width:7px;height:7px;border-radius:50%;background:var(--success);
  box-shadow:0 0 0 0 rgba(63,185,80,.5);animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(63,185,80,.45)}70%{box-shadow:0 0 0 6px rgba(63,185,80,0)}100%{box-shadow:0 0 0 0 rgba(63,185,80,0)}}

.page{max-width:1160px;margin:0 auto;padding:28px 24px 64px}
.page-head{display:flex;align-items:flex-end;justify-content:space-between;gap:16px;margin-bottom:20px}
.page-head .eyebrow{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--fg-3)}
.page-head h1{font-size:21px;margin-top:3px}
.page-head .count{color:var(--fg-3);font-weight:400;font-size:15px}

/* Buttons */
.btn{display:inline-flex;align-items:center;gap:7px;font:inherit;font-weight:600;font-size:13px;
  border-radius:var(--r-sm);padding:9px 15px;border:1px solid transparent;cursor:pointer;transition:.12s}
.btn-primary{background:var(--accent);color:var(--accent-fg)}
.btn-primary:hover{background:var(--accent-2)}
.btn-ghost{background:transparent;color:var(--fg-2);border-color:var(--border-2)}
.btn-ghost:hover{background:var(--surface-2);color:var(--fg)}
.chip-btn{font:inherit;font-size:12.5px;font-weight:500;color:var(--fg-2);cursor:pointer;
  background:var(--surface-2);border:1px solid var(--border);border-radius:999px;padding:5px 11px;transition:.12s}
.chip-btn:hover{border-color:var(--border-2);color:var(--fg);background:var(--raise)}

/* Panels & sections */
.panel{background:var(--surface);border:1px solid var(--border);border-radius:var(--r)}
.panel-h{display:flex;align-items:center;gap:8px;padding:13px 16px;border-bottom:1px solid var(--border)}
.panel-h .ico{color:var(--fg-3)}
.panel-h h3{font-size:13px;font-weight:600;letter-spacing:.01em}
.panel-h .aux{margin-left:auto}
.panel-b{padding:16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:820px){.grid{grid-template-columns:1fr}.page-head{flex-direction:column;align-items:flex-start}}

/* Forms */
label.lbl{display:block;font-size:12px;font-weight:600;color:var(--fg-2);margin-bottom:8px}
textarea{width:100%;min-height:130px;resize:vertical;background:var(--bg);color:var(--fg);
  border:1px solid var(--border-2);border-radius:var(--r-sm);padding:11px 12px;
  font-family:var(--mono);font-size:12.5px;line-height:1.6}
textarea:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 3px rgba(77,124,254,.15)}
.form-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-top:12px}
.samples{display:flex;align-items:center;gap:7px;flex-wrap:wrap}
.samples .sep{width:1px;height:20px;background:var(--border-2);margin:0 2px}
.hint{margin:12px 0 0;font-size:12.5px;color:var(--fg-3)}

/* Tables */
table{width:100%;border-collapse:collapse}
thead th{text-align:left;font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;
  color:var(--fg-3);padding:9px 14px;border-bottom:1px solid var(--border)}
tbody td{padding:11px 14px;border-bottom:1px solid var(--border);font-size:13.5px;vertical-align:middle}
tbody tr:last-child td{border-bottom:0}
.rowlink{cursor:pointer;transition:background .1s}
.rowlink:hover{background:var(--surface-2)}
.cell-title{font-weight:500;color:var(--fg)}
.cell-sub{font-size:12px;color:var(--fg-3);font-family:var(--mono);margin-top:2px}
.kv{width:100%}.kv td{padding:7px 0;border-bottom:1px solid var(--border);font-size:13px}
.kv td:first-child{color:var(--fg-3);width:130px;white-space:nowrap}
.kv tr:last-child td{border-bottom:0}

/* Status pills */
.pill{display:inline-flex;align-items:center;gap:6px;padding:2px 9px;border-radius:var(--r-sm);
  font-size:12px;font-weight:500;line-height:1.7;border:1px solid transparent;white-space:nowrap}
.pill i{width:6px;height:6px;border-radius:50%;background:currentColor;flex:none}
.s-queued{color:#9aa4b2;background:#9aa4b217;border-color:#9aa4b230}
.s-visiting{color:#5b9bff;background:#5b9bff17;border-color:#5b9bff30}
.s-analyzing{color:#a78bfa;background:#a78bfa17;border-color:#a78bfa30}
.s-trapped{color:#f2555a;background:#f2555a17;border-color:#f2555a33}
.s-benign{color:#3fb950;background:#3fb95017;border-color:#3fb95030}
.s-error{color:#e0a23a;background:#e0a23a17;border-color:#e0a23a30}

/* Risk */
.risk{display:inline-flex;align-items:center;gap:7px;padding:3px 10px;border-radius:var(--r-sm);
  font-size:12px;font-weight:600;font-variant-numeric:tabular-nums}
.risk b{font-weight:700}
.rl-critical{color:#f2555a;background:#f2555a15;border:1px solid #f2555a33}
.rl-high{color:#f0883e;background:#f0883e15;border:1px solid #f0883e33}
.rl-medium{color:#e0a23a;background:#e0a23a15;border:1px solid #e0a23a33}
.rl-low{color:#3fb950;background:#3fb95015;border:1px solid #3fb95030}

/* Case header */
.case-head{margin-bottom:20px}
.crumb{display:inline-flex;align-items:center;gap:6px;font-size:13px;color:var(--fg-3);margin-bottom:12px}
.crumb a{color:var(--fg-2)}
.case-title{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.case-title h1{font-size:20px}
.case-meta{display:flex;align-items:center;gap:16px;flex-wrap:wrap;margin-top:10px;font-size:13px;color:var(--fg-2)}
.case-meta .mi{display:inline-flex;align-items:center;gap:6px}
.case-meta .mi .ico{width:14px;height:14px;color:var(--fg-3)}
.case-actions{margin-left:auto}
@media(max-width:820px){.case-actions{margin-left:0;margin-top:12px}}

/* Verdict */
.verdict-line{display:flex;align-items:center;gap:10px;font-weight:600;font-size:15px;margin-bottom:4px}
.verdict-line.phish{color:var(--danger)}.verdict-line.clean{color:var(--success)}
.conf{margin:14px 0}
.conf-top{display:flex;justify-content:space-between;font-size:12px;color:var(--fg-3);margin-bottom:5px}
.bar{height:6px;border-radius:99px;background:var(--surface-2);overflow:hidden}
.bar>span{display:block;height:100%;border-radius:99px;background:var(--accent)}
.flags{list-style:none;margin:12px 0 0;padding:0;display:flex;flex-direction:column;gap:7px}
.flags li{display:flex;gap:9px;font-size:13px;color:var(--fg);align-items:flex-start}
.flags li::before{content:"";width:6px;height:6px;border-radius:50%;background:var(--danger);margin-top:7px;flex:none}
.subhead{font-size:11px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;color:var(--fg-3);margin:16px 0 8px}

/* Timeline */
.timeline{list-style:none;margin:0;padding:0}
.timeline li{position:relative;padding:0 0 20px 34px;min-height:22px}
.timeline li::before{content:"";position:absolute;left:11px;top:22px;bottom:0;width:2px;background:var(--border-2)}
.timeline li:last-child::before{display:none}
.node{position:absolute;left:0;top:0;width:24px;height:24px;border-radius:50%;display:grid;place-items:center;
  background:var(--surface-2);border:1px solid var(--border-2)}
.node .ico{width:13px;height:13px}
.node.n-neutral{color:var(--fg-2)}.node.n-info{color:var(--info)}.node.n-violet{color:var(--violet)}
.node.n-warn{color:var(--warn)}.node.n-danger{color:var(--danger);border-color:#f2555a55;background:#f2555a12}
.t-label{font-weight:500;font-size:13.5px}
.t-detail{color:var(--fg-3);font-size:12.5px;font-family:var(--mono);word-break:break-all;margin-top:2px}
.t-ts{color:var(--fg-3);font-size:12px;margin-top:2px}

/* Email viewer */
.tabs{display:flex;gap:2px;border-bottom:1px solid var(--border);margin:-16px -16px 14px;padding:0 8px}
.tab{background:none;border:0;border-bottom:2px solid transparent;color:var(--fg-3);cursor:pointer;
  font:inherit;font-size:13px;font-weight:500;padding:12px 12px;display:inline-flex;align-items:center;gap:7px}
.tab:hover{color:var(--fg-2)}
.tab.active{color:var(--fg);border-bottom-color:var(--accent)}
.emailframe{width:100%;height:340px;border:1px solid var(--border);border-radius:var(--r-sm);background:#fff}
.pane pre{margin:0;white-space:pre-wrap;background:var(--bg);border:1px solid var(--border);
  border-radius:var(--r-sm);padding:13px;font-size:12px;line-height:1.6;max-height:360px;overflow:auto}
.frame-note{font-size:12px;color:var(--fg-3);margin:7px 0 0}

/* Screenshot */
.shot{width:100%;border-radius:var(--r-sm);border:1px solid var(--border);display:block}
.shot-empty{display:grid;place-items:center;height:200px;border:1px dashed var(--border-2);
  border-radius:var(--r-sm);color:var(--fg-3);font-size:13px}

/* Hits */
.hit-flash{animation:flash 1.1s ease-out}
@keyframes flash{0%{background:#f2555a26}100%{background:transparent}}
.mappin{width:100%;height:220px;border:1px solid var(--border);border-radius:var(--r-sm);margin:14px 16px 0;width:calc(100% - 32px)}
.empty{display:flex;flex-direction:column;align-items:center;gap:10px;padding:40px 16px;text-align:center;color:var(--fg-3)}
.empty .ico{width:26px;height:26px;color:var(--border-2)}
.empty b{color:var(--fg-2);font-weight:600}

/* Report */
.report{margin:0;white-space:pre-wrap;background:var(--bg);border:1px solid var(--border);
  border-radius:var(--r-sm);padding:13px;font-size:12.5px;line-height:1.65;font-family:var(--mono);max-height:360px;overflow:auto}
.banner{display:flex;gap:10px;align-items:flex-start;padding:12px 14px;border-radius:var(--r-sm);
  background:#e0a23a14;border:1px solid #e0a23a33;color:#f0c377;font-size:13px;margin-bottom:20px}
.banner .ico{color:var(--warn);margin-top:1px}
</style></head><body>
<div class=appbar>
  <div class=brand><span class=mark>""" + _icon("shield") + """</span>
    <span>PhishTrap<small>Phishing response console</small></span></div>
  <div class=spacer></div>
  <span class=live><span class=dot></span>Live</span>
</div>"""

_FOOT = "</body></html>"


def chip(status: str) -> str:
    return f'<span class="pill s-{e(status)}"><i></i>{e(status)}</span>'


def render_index(cases: list[dict], samples: list[dict] | None = None) -> str:
    import json as _json
    samples = samples or []
    sample_btns = "".join(
        f'<button type=button class=chip-btn data-i={i}>{e(s["name"])}</button>' for i, s in enumerate(samples)
    )
    samples_json = _json.dumps([s["content"] for s in samples])

    def _row(c: dict) -> str:
        hits = (f'<span class="pill s-trapped"><i></i>{c["hit_count"]}</span>'
                if c["hit_count"] else '<span class=subtle>—</span>')
        brand = e(str(c["brand"])) if c.get("brand") else '<span class=subtle>—</span>'
        return (
            f'<tr class=rowlink data-href="/cases/{c["id"]}">'
            f'<td class="mono subtle">#{c["id"]}</td>'
            f'<td>{chip(c["status"])}</td>'
            f'<td><div class=cell-title>{e(c["subject"] or "(no subject)")[:70]}</div>'
            f'<div class=cell-sub>{e(c["sender"] or "")}</div></td>'
            f'<td>{brand}</td>'
            f'<td>{hits}</td></tr>'
        )

    rows = "".join(_row(c) for c in cases)
    table = (
        f'<table><thead><tr><th>ID</th><th>Status</th><th>Threat</th><th>Brand</th><th>Callbacks</th></tr></thead>'
        f'<tbody id=rows>{rows}</tbody></table>'
    ) if cases else (
        f'<div class=empty>{_icon("inbox")}<b>No cases yet</b>'
        f'<span>Paste a suspicious email above to run it through the sandbox.</span></div>'
    )

    return _HEAD + f"""
    <div class=page>
      <div class=page-head>
        <div><div class=eyebrow>Triage</div><h1>Submit email</h1></div>
      </div>
      <div class=panel>
        <div class=panel-b>
          <form id=f>
            <label class=lbl for=ta>Suspicious email — paste raw .eml or just the body with a link</label>
            <textarea id=ta name=raw_email placeholder="From: ...&#10;Subject: ...&#10;&#10;Verify here: https://..."></textarea>
            <div class=form-actions>
              <button type=submit class="btn btn-primary">{_icon("target")} Analyze &amp; trap</button>
              <div class=samples>
                <span class=sep></span>
                <span class=subtle style="font-size:12px">Samples</span>
                {sample_btns}
              </div>
            </div>
            <p class=hint>Start the decoy site with <code>python demo/fake_phish_site.py</code> so sample links resolve.</p>
          </form>
        </div>
      </div>

      <div class=panel id=preview hidden style="margin-top:16px">
        <div class=panel-b>
          <div class=tabs>
            <button type=button class="tab active" data-t=rendered>{_icon("eye")} Rendered</button>
            <button type=button class="tab" data-t=source>{_icon("code")} Source</button>
          </div>
          <table class=kv id=pmeta style="margin-bottom:14px"></table>
          <div class=pane data-p=rendered>
            <iframe class=emailframe sandbox id=pframe></iframe>
            <p class=frame-note>Sandboxed preview — scripts and navigation disabled.</p>
          </div>
          <div class=pane data-p=source hidden><pre id=psrc></pre></div>
          <div id=pflags style="margin-top:14px"></div>
        </div>
      </div>

      <div class=page-head style="margin-top:32px">
        <div><div class=eyebrow>Queue</div><h1>Cases <span class=count>{len(cases)}</span></h1></div>
      </div>
      <div class=panel>{table}</div>
    </div>
    <script>
    const SAMPLES={samples_json};
    const esc=s=>(s||'').replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
    document.querySelectorAll('.rowlink').forEach(r=>r.onclick=()=>location.href=r.dataset.href);
    async function updatePreview(){{
      const raw=f.raw_email.value.trim();
      const box=document.getElementById('preview');
      if(!raw){{box.hidden=true;return;}}
      const fd=new FormData();fd.append('raw_email',raw);
      const j=await (await fetch('/preview',{{method:'POST',body:fd}})).json();
      box.hidden=false;
      const row=(k,v)=>v?`<tr><td>${{k}}</td><td class=mono>${{esc(v)}}</td></tr>`:'';
      document.getElementById('pmeta').innerHTML=
        row('From',j.from)+row('Reply-To',j.reply_to)+row('Return-Path',j.return_path)+row('Subject',j.subject);
      const body=j.html||('<pre style=\"font:14px/1.5 system-ui;white-space:pre-wrap;padding:16px\">'+esc(j.text||'(empty)')+'</pre>');
      document.getElementById('pframe').srcdoc=
        '<!doctype html><meta charset=utf-8><base target=_blank><style>body{{margin:0;background:#fff;color:#111}}</style>'+body;
      document.getElementById('psrc').textContent=j.raw||'';
      document.getElementById('pflags').innerHTML=
        (j.flags&&j.flags.length)?'<div class=subhead>Red flags</div><ul class=flags>'+j.flags.map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul>':'';
    }}
    document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{{
      document.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===t));
      document.querySelectorAll('#preview .pane').forEach(p=>p.hidden=p.dataset.p!==t.dataset.t);
    }});
    document.querySelectorAll('.chip-btn').forEach(b=>b.onclick=()=>{{
      f.raw_email.value=SAMPLES[+b.dataset.i]; updatePreview(); f.raw_email.scrollIntoView({{block:'nearest'}});
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
    return e(" ".join(p for p in parts if p).strip()) or "<span class=subtle>—</span>"


def _map_iframe(hits: list[dict]) -> str:
    for h in hits:
        g = h.get("geo") or {}
        if g.get("lat") is not None and g.get("lon") is not None:
            lat, lon = g["lat"], g["lon"]
            d = 4
            bbox = f"{lon-d},{lat-d},{lon+d},{lat+d}"
            src = (f"https://www.openstreetmap.org/export/embed.html?bbox={bbox}"
                   f"&marker={lat},{lon}&layer=mapnik")
            return f"<iframe class=mappin src='{e(src)}' loading=lazy></iframe>"
    return ""


def _panel(title: str, icon: str, body: str, aux: str = "") -> str:
    aux_html = f'<div class=aux>{aux}</div>' if aux else ""
    return (f'<div class=panel><div class=panel-h>{_icon(icon)}<h3>{e(title)}</h3>{aux_html}</div>'
            f'<div class=panel-b>{body}</div></div>')


def render_case(c: dict, abuse: str) -> str:
    from . import report
    v = c.get("verdict") or {}
    sb = c.get("sandbox") or {}
    email = c.get("email") or {}
    score, level = report.risk_score(c)

    # Timeline
    def _tl(ev: dict) -> str:
        icon, ncls = TL_MAP.get(ev.get("icon", ""), ("clock", "n-neutral"))
        detail = f"<div class=t-detail>{e(ev['detail'])}</div>" if ev.get("detail") else ""
        ts = f"<div class=t-ts>{e(ev['ts'])}</div>" if ev.get("ts") else ""
        return (f'<li><span class="node {ncls}">{_icon(icon)}</span>'
                f'<div class=t-label>{e(ev["label"])}</div>{detail}{ts}</li>')
    timeline = f'<ul class=timeline>{"".join(_tl(x) for x in report.build_timeline(c))}</ul>'

    # Email viewer
    rendered_body = email.get("html") or (
        "<pre style='font:14px/1.5 system-ui;white-space:pre-wrap;padding:16px'>"
        + e(email.get("text") or email.get("body_preview") or "(empty)") + "</pre>")
    doc = ("<!doctype html><meta charset=utf-8><base target=_blank>"
           "<style>body{margin:0;background:#fff;color:#111}</style>" + rendered_body)
    hdr = lambda k, val: f"<tr><td>{k}</td><td class=mono>{e(str(val))}</td></tr>" if val else ""
    email_meta = (hdr("From", email.get("from")) + hdr("Reply-To", email.get("reply_to"))
                  + hdr("Return-Path", email.get("return_path")) + hdr("Subject", email.get("subject")))
    email_viewer = f"""
      <div class=tabs>
        <button type=button class="tab active" data-t=rendered>{_icon("eye")} Rendered</button>
        <button type=button class="tab" data-t=source>{_icon("code")} Source</button>
      </div>
      <table class=kv style="margin-bottom:14px">{email_meta}</table>
      <div class=pane data-p=rendered>
        <iframe class=emailframe sandbox srcdoc="{e(doc)}"></iframe>
        <p class=frame-note>Sandboxed — scripts and navigation disabled.</p></div>
      <div class=pane data-p=source hidden><pre>{e(email.get('raw') or '')}</pre></div>"""

    # Sandbox
    if c.get("screenshot"):
        shot = f'<img class=shot src="/shots/{e(c["screenshot"])}" alt="captured page">'
    else:
        shot = '<div class=shot-empty>No screenshot captured</div>'
    sb_meta = (f'<table class=kv style="margin-top:14px">'
               f'{hdr("Target", c.get("target_url"))}{hdr("Final URL", c.get("final_url"))}'
               f'{hdr("Resolved IP", sb.get("ip"))}</table>')

    # Verdict
    is_phish = v.get("is_credential_phish")
    conf = v.get("confidence")
    conf_pct = f"{conf:.0%}" if isinstance(conf, (int, float)) else "—"
    conf_bar = (f'<div class=conf><div class=conf-top><span>Confidence</span><span>{conf_pct}</span></div>'
                f'<div class=bar><span style="width:{int((conf or 0)*100)}%"></span></div></div>'
                if v else "")
    brand = v.get("impersonated_brand")
    brand_html = (f' · impersonating <b style="color:var(--fg)">{e(str(brand))}</b>'
                  if brand and brand not in ("unknown", "") else "")
    flags = "".join(f"<li>{e(fl)}</li>" for fl in email.get("flags", []))
    flags_block = (f'<div class=subhead>Email red flags</div><ul class=flags>{flags}</ul>'
                   if flags else '<div class=subhead>Email red flags</div><p class=subtle style="font-size:13px">None detected.</p>')
    reasoning = v.get("reasoning") or ""
    reasoning_html = f'<p style="font-size:13.5px;margin:6px 0 0">{e(str(reasoning))}</p>' if reasoning else ""
    detected_by = f"Detected by {e(v.get('source', 'heuristic'))}" if v else ""
    verdict_icon = _icon("alert") if is_phish else _icon("shield")
    verdict_word = "Credential phishing" if is_phish else "Not a credential phish"
    verdict_body = (
        f'<div class="verdict-line {"phish" if is_phish else "clean"}">{verdict_icon}{verdict_word}</div>'
        f'<p class=subtle style="font-size:12.5px;margin:2px 0 0">{detected_by}{brand_html}</p>'
        f'{conf_bar}{reasoning_html}{flags_block}')

    # Hits
    hit_rows = "".join(
        f'<tr class=hit-flash><td class="mono subtle">{e(h["ts"])}</td>'
        f'<td class=mono>{e(h["ip"] or "")}</td><td>{_geo_str(h)}</td>'
        f'<td class="subtle" style="font-size:12px">{e((h["ua"] or "")[:40])}</td></tr>'
        for h in c.get("hits", []))
    if hit_rows:
        hits_table = (f'<table><thead><tr><th>When</th><th>IP</th><th>Location</th><th>User-Agent</th></tr></thead>'
                      f'<tbody>{hit_rows}</tbody></table>{_map_iframe(c.get("hits", []))}')
    else:
        hits_table = (f'<div class=empty>{_icon("target")}<b>No callbacks yet</b>'
                      f'<span>Trigger the planted canary to see the attacker appear here, live.</span></div>')

    # Canaries
    canary_items = "".join(
        f'<li style="margin-bottom:8px"><code>{e(cn["url"])}</code><br>'
        f'<span class=subtle style="font-size:12.5px">decoy {e(cn["persona"]["full_name"])} · {e(cn["persona"]["email"])}</span></li>'
        for cn in c.get("canaries", []))
    canary_body = (f'<ul style="list-style:none;margin:0;padding:0">{canary_items}</ul>'
                   if canary_items else
                   '<p class=subtle style="font-size:13px;margin:0">No canary planted — the page was not flagged as a credential phish.</p>')

    # IOCs
    ioc_rows = "".join(
        f'<tr><td class="subtle" style="width:150px">{e(i["type"])}</td><td class=mono>{e(i["value"])}</td></tr>'
        for i in c.get("iocs", [])) or '<tr><td colspan=2 class=subtle>No indicators.</td></tr>'

    err_banner = (f'<div class=banner>{_icon("alert")}<div><b>Processing error.</b> '
                  f'{e((c.get("error") or "")[:300])}</div></div>' if c.get("status") == "error" else "")

    received = e(c.get("created_at") or "")

    return _HEAD + f"""
    <div class=page>
      <div class=case-head>
        <div class=crumb><a href='/'>Cases</a> / <span>#{c['id']}</span></div>
        <div class=case-title>
          <h1>{e((email.get('subject') or 'Case #'+str(c['id']))[:80])}</h1>
          {chip(c['status'])}
          <span class="risk rl-{level}">RISK <b>{score}</b> · {level.upper()}</span>
          <div class=case-actions>
            <a class="btn btn-ghost" href='/cases/{c['id']}/iocs'>{_icon("download")} Export IOCs</a>
          </div>
        </div>
        <div class=case-meta>
          <span class=mi>{_icon("mail")} {e(email.get('from') or 'unknown sender')}</span>
          <span class=mi>{_icon("clock")} {received}</span>
          {f'<span class=mi>{_icon("globe")} {e(c.get("final_url") or c.get("target_url") or "")}</span>' if (c.get('final_url') or c.get('target_url')) else ''}
        </div>
      </div>
      {err_banner}

      <div class=grid>
        {_panel("Reported email", "mail", email_viewer)}
        {_panel("Verdict", "cpu", verdict_body)}
      </div>

      <div class=grid style="margin-top:16px">
        {_panel("Sandbox capture", "eye", shot + sb_meta)}
        {_panel("Timeline", "clock", timeline)}
      </div>

      <div style="margin-top:16px">
        <div class=panel>
          <div class=panel-h>{_icon("target")}<h3>Canary trap</h3></div>
          <div class=panel-b>{canary_body}</div>
          <div class=panel-h style="border-top:1px solid var(--border)">{_icon("alert")}<h3>Attacker callbacks</h3></div>
          {hits_table}
        </div>
      </div>

      <div class=grid style="margin-top:16px">
        {_panel("Indicators of compromise", "globe", f'<table>{ioc_rows}</table>')}
        {_panel("Abuse report", "external", f'<pre class=report>{e(abuse)}</pre>')}
      </div>
    </div>
    <script>
    document.querySelectorAll('.tab').forEach(t=>t.onclick=()=>{{
      const scope=t.closest('.panel-b');
      scope.querySelectorAll('.tab').forEach(x=>x.classList.toggle('active',x===t));
      scope.querySelectorAll('.pane').forEach(p=>p.hidden=p.dataset.p!==t.dataset.t);
    }});
    const es=new EventSource('/events');
    es.addEventListener('hit',ev=>{{if(JSON.parse(ev.data).case_id=={c['id']})location.reload();}});
    es.addEventListener('case',ev=>{{if(JSON.parse(ev.data).id=={c['id']})location.reload();}});
    </script>""" + _FOOT
