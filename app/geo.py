"""Best-effort IP geolocation for canary hits. Uses the free ip-api.com endpoint
with a short timeout and graceful fallback so the demo never blocks."""
import ipaddress
import json
import urllib.request
from functools import lru_cache


def _flag(cc: str) -> str:
    if len(cc) != 2 or not cc.isalpha():
        return "🏳️"
    return "".join(chr(0x1F1E6 + ord(ch) - ord("A")) for ch in cc.upper())


@lru_cache(maxsize=256)
def lookup(ip: str) -> dict:
    """Return {city, country, cc, flag, lat, lon} or a local/unknown marker."""
    try:
        addr = ipaddress.ip_address(ip)
        if addr.is_private or addr.is_loopback:
            return {"city": "Local / private network", "country": "", "cc": "",
                    "flag": "🏠", "lat": None, "lon": None}
    except ValueError:
        return {"city": "unknown", "country": "", "cc": "", "flag": "🏳️", "lat": None, "lon": None}
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,city,country,countryCode,lat,lon"
        with urllib.request.urlopen(url, timeout=2) as r:
            d = json.load(r)
        if d.get("status") == "success":
            return {"city": d.get("city") or "", "country": d.get("country") or "",
                    "cc": d.get("countryCode") or "", "flag": _flag(d.get("countryCode") or ""),
                    "lat": d.get("lat"), "lon": d.get("lon")}
    except Exception:
        pass
    return {"city": "unknown", "country": "", "cc": "", "flag": "🏳️", "lat": None, "lon": None}
