import hashlib
import re
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from html.parser import HTMLParser
from urllib.parse import urlparse

URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.I)
HEADER_RE = re.compile(r"^[A-Za-z-]+:\s", re.M)


class _LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[dict] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            self.links.append({"href": self._href, "text": "".join(self._text).strip()})
            self._href = None


def domain_of(value: str) -> str:
    if "@" in value and "://" not in value:
        return value.rsplit("@", 1)[-1].strip(">").lower()
    return (urlparse(value).hostname or "").lower()


def parse_email(raw: bytes) -> dict:
    """Parse a raw .eml (or pasted body text) into headers, links and red flags."""
    looks_like_eml = bool(HEADER_RE.match(raw.decode(errors="ignore").lstrip()[:200]))
    if looks_like_eml:
        msg = BytesParser(policy=policy.default).parsebytes(raw)
    else:
        msg = BytesParser(policy=policy.default).parsebytes(b"Content-Type: text/plain\n\n" + raw)

    text_parts, html_parts, attachments = [], [], []
    for part in msg.walk():
        if part.is_multipart():
            continue
        if part.get_filename():
            payload = part.get_payload(decode=True) or b""
            attachments.append(
                {"name": part.get_filename(), "sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)}
            )
        elif part.get_content_type() == "text/html":
            html_parts.append(part.get_content())
        elif part.get_content_type() == "text/plain":
            text_parts.append(part.get_content())

    links: list[dict] = []
    for html in html_parts:
        p = _LinkParser()
        p.feed(html)
        links += [l for l in p.links if l["href"].lower().startswith(("http://", "https://"))]
    seen = {l["href"] for l in links}
    for url in URL_RE.findall("\n".join(text_parts + html_parts)):
        url = url.rstrip(".,;")
        if url not in seen:
            seen.add(url)
            links.append({"href": url, "text": ""})

    from_name, from_addr = parseaddr(str(msg.get("From", "")))
    _, reply_to = parseaddr(str(msg.get("Reply-To", "")))
    _, return_path = parseaddr(str(msg.get("Return-Path", "")))
    auth = str(msg.get("Authentication-Results", ""))

    flags = []
    if reply_to and domain_of(reply_to) != domain_of(from_addr):
        flags.append(f"Reply-To domain ({domain_of(reply_to)}) differs from From ({domain_of(from_addr)})")
    if return_path and domain_of(return_path) != domain_of(from_addr):
        flags.append(f"Return-Path domain ({domain_of(return_path)}) differs from From")
    for mech in ("spf", "dkim", "dmarc"):
        m = re.search(rf"{mech}=(\w+)", auth, re.I)
        if m and m.group(1).lower() not in ("pass", "none"):
            flags.append(f"{mech.upper()} {m.group(1).lower()}")
    for l in links:
        shown = URL_RE.search(l["text"] or "")
        if shown and domain_of(shown.group()) != domain_of(l["href"]):
            flags.append(f"Link text shows {domain_of(shown.group())} but points to {domain_of(l['href'])}")

    return {
        "subject": str(msg.get("Subject", "(no subject)")),
        "from_name": from_name,
        "from": from_addr,
        "reply_to": reply_to,
        "return_path": return_path,
        "received": [str(h) for h in msg.get_all("Received", [])],
        "auth_results": auth,
        "links": links,
        "attachments": attachments,
        "body_preview": ("\n".join(text_parts) or re.sub(r"<[^>]+>", " ", "\n".join(html_parts)))[:1500],
        "flags": flags,
        "raw": raw.decode(errors="replace"),
        "html": "\n".join(html_parts),
        "text": "\n".join(text_parts),
    }
