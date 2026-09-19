"""
fixer.ai — Central configuration
Loads from .env file; provides typed settings used across the whole backend.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root (two levels up from backend/config.py)
_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / ".env")

# ── Database ──────────────────────────────────────────────────────────────────
DATABASE_URL: str = os.getenv(
    "DATABASE_URL", f"sqlite+aiosqlite:///{_ROOT / 'backend' / 'database' / 'fixer.db'}"
)

# ── Chroma ────────────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR: str = os.getenv(
    "CHROMA_PERSIST_DIR", str(_ROOT / "data" / "chroma_db")
)

# ── Ollama / LLM ──────────────────────────────────────────────────────────────
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
VISION_MODEL: str = os.getenv("VISION_MODEL", "gemma3:4b")
REASONING_MODEL: str = os.getenv("REASONING_MODEL", "phi4-mini")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# LLM_STUB_MODE: when True, all LLM/embedding calls return deterministic mock data.
# Toggle to False when running on capable hardware with Ollama installed.
LLM_STUB_MODE: bool = os.getenv("LLM_STUB_MODE", "true").lower() == "true"

# ── Slack ─────────────────────────────────────────────────────────────────────
SLACK_BOT_TOKEN: str = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN: str = os.getenv("SLACK_APP_TOKEN", "")
SLACK_ESCALATION_CHANNEL: str = os.getenv("SLACK_ESCALATION_CHANNEL", "#fixer-ai-escalations")

# ── Simulation ────────────────────────────────────────────────────────────────
SIM_CLOCK_MULTIPLIER: float = float(os.getenv("SIM_CLOCK_MULTIPLIER", "600"))
SIM_TICK_INTERVAL: float = float(os.getenv("SIM_TICK_INTERVAL", "1.0"))

# ── Admin ─────────────────────────────────────────────────────────────────────
ADMIN_SECRET_KEY: str = os.getenv("ADMIN_SECRET_KEY", "dev-secret")

# ── CORS ──────────────────────────────────────────────────────────────────────
FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

# ── Manual data directory ─────────────────────────────────────────────────────
MANUALS_DIR: Path = _ROOT / "data" / "manuals"
MANUALS_DIR.mkdir(parents=True, exist_ok=True)
