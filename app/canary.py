import secrets

from faker import Faker

from . import db
from .config import CANARY_BASE_URL

fake = Faker()


def mint(case_id: int) -> dict:
    """Generate a fake persona whose data carries a unique canary callback URL."""
    token = secrets.token_urlsafe(9)
    url = f"{CANARY_BASE_URL}/c/{token}"
    profile = fake.simple_profile()
    first, _, last = profile["name"].partition(" ")
    persona = {
        "token": token,
        "canary_url": url,
        "full_name": profile["name"],
        "username": profile["username"],
        # Password is itself the tripwire: a URL. If the attacker's harvested
        # data is ever pasted into a browser / scanned, the canary fires.
        "password": url,
        "email": f"{profile['username']}@{fake.free_email_domain()}",
        # A real inbox-shaped bait + the callback again, for form fields that
        # expect a "recovery"/"website" value.
        "recovery_email": f"recover-{token}@example-mail.com",
        "website": url,
        "phone": fake.phone_number(),
    }
    db.add_canary(token, case_id, url, persona)
    return persona


def value_for_role(persona: dict, role: str) -> str:
    """Map an agent-identified field role to the fake value to type in."""
    role = (role or "").lower()
    mapping = {
        "email": persona["email"],
        "username": persona["username"],
        "user": persona["username"],
        "password": persona["password"],
        "pass": persona["password"],
        "pin": secrets.randbelow(9000).__add__(1000).__str__(),
        "phone": persona["phone"],
        "name": persona["full_name"],
        "website": persona["website"],
        # A well-known test card number (Luhn-valid, never a real account).
        "card": "4111111111111111",
        "recovery": persona["recovery_email"],
        "otp": secrets.randbelow(900000).__add__(100000).__str__(),
    }
    for key, val in mapping.items():
        if key in role:
            return val
    return persona["canary_url"]
