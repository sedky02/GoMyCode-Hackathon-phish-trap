import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
SHOTS_DIR = DATA_DIR / "shots"
SHOTS_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "phishtrap.db"

CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
CANARY_BASE_URL = os.getenv("CANARY_BASE_URL", "http://localhost:8000").rstrip("/")
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "local")
SANDBOX_IMAGE = os.getenv("SANDBOX_IMAGE", "phishtrap-sandbox")
SUBMIT_THRESHOLD = float(os.getenv("SUBMIT_THRESHOLD", "0.6"))
