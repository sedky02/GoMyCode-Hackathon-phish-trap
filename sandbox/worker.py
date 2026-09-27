"""Isolated browser visit. Runs standalone (also inside Docker) and prints JSON.

Usage: python -m sandbox.worker <url> <screenshot_path>
Output on stdout: {"final_url", "redirects", "ip", "forms", "error"}
Never submits anything here; submission is a separate, deliberate step.
"""
import json
import socket
import sys
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

FORM_JS = """
() => [...document.querySelectorAll('form')].map((f, fi) => ({
  index: fi,
  action: f.action || location.href,
  method: (f.method || 'get').toLowerCase(),
  fields: [...f.querySelectorAll('input,select,textarea')]
    .filter(e => !['hidden','submit','button','image'].includes(e.type))
    .map(e => ({
      selector: `form:nth-of-type(${fi+1}) [name="${e.name}"]`,
      name: e.name || '', id: e.id || '', type: e.type || 'text',
      placeholder: e.placeholder || '',
      label: (e.labels && e.labels[0] && e.labels[0].innerText || '').trim().slice(0,60),
      autocomplete: e.autocomplete || '',
    })),
  submit_selector: (() => {
    const b = f.querySelector('[type=submit],button');
    return b ? `form:nth-of-type(${fi+1}) ${b.tagName.toLowerCase()}${b.type?`[type="${b.type}"]`:''}` : null;
  })(),
}))
"""


def visit(url: str, screenshot_path: str) -> dict:
    redirects: list[str] = []
    out: dict = {"final_url": url, "redirects": redirects, "ip": None, "forms": [], "error": None}
    try:
        out["ip"] = socket.gethostbyname(urlparse(url).hostname or "")
    except Exception:
        pass
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            ctx = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                viewport={"width": 1280, "height": 900},
                accept_downloads=False,
            )
            page = ctx.new_page()
            page.on("response", lambda r: redirects.append(r.url) if 300 <= r.status < 400 else None)
            page.on("dialog", lambda d: d.dismiss())
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
            out["final_url"] = page.url
            page.screenshot(path=screenshot_path, full_page=False)
            out["forms"] = page.evaluate(FORM_JS)
            browser.close()
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


if __name__ == "__main__":
    print(json.dumps(visit(sys.argv[1], sys.argv[2])))
