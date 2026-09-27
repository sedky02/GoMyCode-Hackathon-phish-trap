import json
import sqlite3
import threading
from datetime import datetime, timezone

from .config import DB_PATH

_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
_conn.row_factory = sqlite3.Row
_lock = threading.Lock()

_conn.executescript(
    """
    CREATE TABLE IF NOT EXISTS cases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        subject TEXT, sender TEXT,
        status TEXT NOT NULL,
        target_url TEXT, final_url TEXT,
        email_json TEXT, sandbox_json TEXT, verdict_json TEXT,
        screenshot TEXT, submitted INTEGER DEFAULT 0, error TEXT
    );
    CREATE TABLE IF NOT EXISTS iocs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_id INTEGER NOT NULL, type TEXT NOT NULL, value TEXT NOT NULL,
        UNIQUE(case_id, type, value)
    );
    CREATE TABLE IF NOT EXISTS canaries (
        token TEXT PRIMARY KEY, case_id INTEGER NOT NULL,
        url TEXT NOT NULL, persona_json TEXT NOT NULL, created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS hits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT NOT NULL, case_id INTEGER, ip TEXT, ua TEXT,
        headers_json TEXT, ts TEXT NOT NULL
    );
    """
)

JSON_COLS = ("email_json", "sandbox_json", "verdict_json")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _exec(sql: str, args=()) -> sqlite3.Cursor:
    with _lock:
        cur = _conn.execute(sql, args)
        _conn.commit()
        return cur


def _query(sql: str, args=()) -> list[dict]:
    with _lock:
        return [dict(r) for r in _conn.execute(sql, args).fetchall()]


def _decode(row: dict) -> dict:
    for col in JSON_COLS:
        if col in row:
            row[col.removesuffix("_json")] = json.loads(row.pop(col) or "null")
    return row


def create_case(subject: str, sender: str, email: dict) -> int:
    cur = _exec(
        "INSERT INTO cases (created_at, subject, sender, status, email_json) VALUES (?,?,?,?,?)",
        (now(), subject, sender, "queued", json.dumps(email)),
    )
    return cur.lastrowid


def update_case(case_id: int, **fields) -> None:
    for col in JSON_COLS:
        key = col.removesuffix("_json")
        if key in fields:
            fields[col] = json.dumps(fields.pop(key))
    cols = ", ".join(f"{k} = ?" for k in fields)
    _exec(f"UPDATE cases SET {cols} WHERE id = ?", (*fields.values(), case_id))


def add_iocs(case_id: int, iocs: list[tuple[str, str]]) -> None:
    with _lock:
        _conn.executemany(
            "INSERT OR IGNORE INTO iocs (case_id, type, value) VALUES (?,?,?)",
            [(case_id, t, v) for t, v in iocs if v],
        )
        _conn.commit()


def list_cases() -> list[dict]:
    return _query(
        """SELECT c.id, c.created_at, c.subject, c.sender, c.status, c.target_url, c.submitted,
                  json_extract(c.verdict_json, '$.impersonated_brand') AS brand,
                  (SELECT COUNT(*) FROM hits h WHERE h.case_id = c.id) AS hit_count
           FROM cases c ORDER BY c.id DESC"""
    )


def get_case(case_id: int) -> dict | None:
    rows = _query("SELECT * FROM cases WHERE id = ?", (case_id,))
    if not rows:
        return None
    case = _decode(rows[0])
    case["iocs"] = _query("SELECT type, value FROM iocs WHERE case_id = ? ORDER BY type", (case_id,))
    case["canaries"] = [
        {**c, "persona": json.loads(c.pop("persona_json"))}
        for c in _query("SELECT * FROM canaries WHERE case_id = ?", (case_id,))
    ]
    case["hits"] = [
        {**h, "headers": json.loads(h.pop("headers_json"))}
        for h in _query("SELECT * FROM hits WHERE case_id = ? ORDER BY id DESC", (case_id,))
    ]
    return case


def add_canary(token: str, case_id: int, url: str, persona: dict) -> None:
    _exec(
        "INSERT INTO canaries (token, case_id, url, persona_json, created_at) VALUES (?,?,?,?,?)",
        (token, case_id, url, json.dumps(persona), now()),
    )


def find_canary(token: str) -> dict | None:
    rows = _query("SELECT * FROM canaries WHERE token = ?", (token,))
    return rows[0] if rows else None


def record_hit(token: str, case_id: int | None, ip: str, ua: str, headers: dict) -> dict:
    ts = now()
    _exec(
        "INSERT INTO hits (token, case_id, ip, ua, headers_json, ts) VALUES (?,?,?,?,?,?)",
        (token, case_id, ip, ua, json.dumps(headers), ts),
    )
    return {"token": token, "case_id": case_id, "ip": ip, "ua": ua, "ts": ts}
