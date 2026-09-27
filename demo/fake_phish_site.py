"""Stand-in 'attacker' phishing pages for the demo. Serves a few fake login/verify
forms and logs whatever gets submitted (as a real kit would). Run:
    python demo/fake_phish_site.py   # http://localhost:9000
Routes:
    /login   ExampleBank — email + password
    /o365    Microsoft 365 — email + password
    /verify  "Identity verification" — name, email, phone, card, recovery email
    /gift    benign-looking promo page with NO credential form (demo the 'benign' verdict)
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

CSS = """<style>body{font:16px system-ui;background:#f0f3f8;display:flex;justify-content:center;
padding-top:50px}.box{background:#fff;padding:32px;border-radius:12px;box-shadow:0 8px 30px #0002;width:340px}
h1{font-size:22px;margin:0 0 4px}p{color:#667;margin:0 0 18px;font-size:14px}
input{width:100%;box-sizing:border-box;padding:11px;margin:6px 0;border:1px solid #cbd5e1;border-radius:8px}
button{width:100%;padding:12px;color:#fff;border:0;border-radius:8px;font-weight:700;margin-top:10px}</style>"""


def form(title, sub, action, fields, color):
    inputs = "".join(
        f'<input name="{n}" type="{t}" placeholder="{p}" required>' for n, t, p in fields
    )
    return (f"<!doctype html><meta charset=utf-8><title>{title}</title>{CSS}"
            f"<div class=box><h1 style='color:{color}'>{title}</h1><p>{sub}</p>"
            f"<form method=post action={action}>{inputs}"
            f"<button style='background:{color}' type=submit>Continue</button></form></div>")


PAGES = {
    "/login": form("ExampleBank", "Sign in to your account", "/login",
                   [("email", "email", "Email address"), ("password", "password", "Password")], "#123c7a"),
    "/o365": form("Microsoft 365", "Sign in to continue to Outlook", "/o365",
                  [("email", "email", "Email, phone, or Skype"), ("password", "password", "Password")], "#0067b8"),
    "/verify": form("Identity Verification", "Confirm your details to unlock your account", "/verify",
                    [("name", "text", "Full name"), ("email", "email", "Email"),
                     ("phone", "tel", "Phone number"), ("card", "text", "Card number"),
                     ("recovery_email", "email", "Recovery email")], "#b91c1c"),
    "/gift": ("<!doctype html><meta charset=utf-8><title>You won a gift card</title>" + CSS +
              "<div class=box><h1 style='color:#059669'>Congratulations!</h1>"
              "<p>You've been selected for a $500 gift card. No form here — this page just "
              "tries to look legit. Great for showing a <b>benign</b> verdict (no credential form).</p></div>"),
}


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        body = PAGES.get(path, PAGES["/login"])
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(body.encode())

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        data = parse_qs(self.rfile.read(n).decode())
        print(f"\n[HARVESTED @ {self.path}]", {k: v[0] for k, v in data.items()}, flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(b"<h2>Thank you, you are now signed in.</h2>")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    print("Fake phishing site on http://localhost:9000  (routes: /login /o365 /verify /gift)")
    HTTPServer(("0.0.0.0", 9000), H).serve_forever()
