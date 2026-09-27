"""Fill a phishing form with fake canary data and submit exactly once.

Usage: python -m sandbox.submit <url> <plan_json>
plan_json: {"fills": [{"selector","value"}], "submit_selector": str|null}
Output: {"posted_to": [urls], "final_url", "error"} — the POST endpoints observed
are the attacker's harvesting backend (a high-value IOC).
"""
import json
import sys

from playwright.sync_api import sync_playwright


def submit(url: str, plan: dict) -> dict:
    posted: list[str] = []
    out = {"posted_to": posted, "final_url": url, "error": None}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            ctx = browser.new_context(accept_downloads=False)
            page = ctx.new_page()
            page.on("dialog", lambda d: d.dismiss())
            page.on(
                "request",
                lambda r: posted.append(r.url) if r.method == "POST" else None,
            )
            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            for fill in plan.get("fills", []):
                try:
                    page.fill(fill["selector"], fill["value"], timeout=4000)
                except Exception:
                    pass
            sel = plan.get("submit_selector")
            try:
                if sel:
                    page.click(sel, timeout=4000)
                else:
                    page.keyboard.press("Enter")
                page.wait_for_timeout(2500)
            except Exception as e:
                out["error"] = f"submit: {type(e).__name__}: {e}"
            out["final_url"] = page.url
            browser.close()
    except Exception as e:
        out["error"] = f"{type(e).__name__}: {e}"
    return out


if __name__ == "__main__":
    print(json.dumps(submit(sys.argv[1], json.loads(sys.argv[2]))))
