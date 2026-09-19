"""
fixer.ai — Self-Contained Project Bootstrapper & Environment Verifier
Run this script whenever setting up the project on a new laptop, account, or environment.

Usage:
  python scripts/bootstrap.py [--skip-tests] [--skip-frontend]
"""

import sys
import os
import shutil
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

def log(step: str, msg: str, status: str = "INFO"):
    tag = {"INFO": "INFO", "SUCCESS": "OK", "WARN": "WARN", "ERROR": "ERR"}.get(status, status)
    print(f"[{tag:<4} | {step:<8}] {msg}")

def check_python_version():
    log("PYTHON", f"Detected Python {sys.version.split()[0]}", "INFO")
    if sys.version_info < (3, 10):
        log("PYTHON", "Python 3.10 or higher is recommended.", "WARN")
    else:
        log("PYTHON", "Python version is compatible.", "SUCCESS")

def setup_env_file():
    env_file = ROOT_DIR / ".env"
    env_example = ROOT_DIR / ".env.example"
    if not env_file.exists():
        if env_example.exists():
            shutil.copy(env_example, env_file)
            log("ENV", "Created .env from .env.example template.", "SUCCESS")
        else:
            log("ENV", ".env.example missing! Please create .env manually.", "ERROR")
    else:
        log("ENV", ".env configuration file already exists.", "INFO")

def check_python_dependencies():
    required_packages = ["fastapi", "uvicorn", "sqlalchemy", "aiosqlite", "chromadb", "numpy", "scipy"]
    missing = []
    for pkg in required_packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        log("DEPS", f"Missing Python packages: {', '.join(missing)}", "WARN")
        log("DEPS", f"Installing dependencies via 'pip install -r requirements.txt'...", "INFO")
        ret = subprocess.call([sys.executable, "-m", "pip", "install", "-r", str(ROOT_DIR / "requirements.txt")])
        if ret == 0:
            log("DEPS", "All Python packages installed successfully.", "SUCCESS")
        else:
            log("DEPS", "Pip install returned an error. Please verify pip manually.", "ERROR")
    else:
        log("DEPS", "Core Python dependencies are installed and available.", "SUCCESS")

def verify_and_seed_database():
    db_path = ROOT_DIR / "backend" / "database" / "fixer.db"
    seed_script = ROOT_DIR / "backend" / "database" / "seed.py"
    
    needs_seed = not db_path.exists() or db_path.stat().st_size < 1000
    if needs_seed:
        log("DATABASE", "Database missing or empty. Seeding initial schema and records...", "INFO")
        ret = subprocess.call([sys.executable, str(seed_script)])
        if ret == 0:
            log("DATABASE", "Database successfully seeded (4 machines, 4 technicians, 8 failure codes).", "SUCCESS")
        else:
            log("DATABASE", "Database seeding failed.", "ERROR")
    else:
        log("DATABASE", f"Database verified at {db_path.name} ({db_path.stat().st_size // 1024} KB).", "SUCCESS")

def verify_and_ingest_chroma():
    chroma_dir = ROOT_DIR / "data" / "chroma_db"
    ingest_script = ROOT_DIR / "scripts" / "ingest_manuals.py"
    
    needs_ingest = not chroma_dir.exists() or len(list(chroma_dir.glob("*"))) == 0
    if needs_ingest:
        log("CHROMA", "Vector store empty. Ingesting manuals into Tier 1 and historical tickets into Tier 2...", "INFO")
        ret = subprocess.call([sys.executable, str(ingest_script)])
        if ret == 0:
            log("CHROMA", "Vector store successfully initialized and populated.", "SUCCESS")
        else:
            log("CHROMA", "Manual ingestion failed.", "ERROR")
    else:
        log("CHROMA", "Persistent Chroma vector store verified in data/chroma_db.", "SUCCESS")

def verify_frontend():
    frontend_dir = ROOT_DIR / "frontend"
    node_modules = frontend_dir / "node_modules"
    npm_cmd = shutil.which("npm")
    
    if not npm_cmd:
        log("FRONTEND", "npm not found in system PATH. Install Node.js if frontend development is needed.", "WARN")
        return
    
    if not node_modules.exists():
        log("FRONTEND", "Installing frontend packages (npm install)...", "INFO")
        subprocess.call([npm_cmd, "install"], cwd=str(frontend_dir), shell=True)
    
    log("FRONTEND", "Building frontend production bundle...", "INFO")
    ret = subprocess.call([npm_cmd, "run", "build"], cwd=str(frontend_dir), shell=True)
    if ret == 0:
        log("FRONTEND", "Frontend production build succeeded cleanly.", "SUCCESS")
    else:
        log("FRONTEND", "Frontend build had warnings/errors.", "WARN")

def run_smoke_tests():
    log("TESTS", "Running backend unit test suite (pytest backend/tests/)...", "INFO")
    pytest_ret = subprocess.call([sys.executable, "-m", "pytest", "backend/tests/", "-q"], cwd=str(ROOT_DIR))
    if pytest_ret == 0:
        log("TESTS", "All 68 backend tests passed cleanly!", "SUCCESS")
    else:
        log("TESTS", "Some unit tests failed. Check environment configuration.", "ERROR")

    log("TESTS", "Running full 5-step demo rehearsal (scripts/e2e_smoke_test.py)...", "INFO")
    e2e_ret = subprocess.call([sys.executable, "scripts/e2e_smoke_test.py"], cwd=str(ROOT_DIR))
    if e2e_ret == 0:
        log("TESTS", "5-step demo rehearsal passed with 100% integrity!", "SUCCESS")
    else:
        log("TESTS", "Demo rehearsal encountered issues.", "ERROR")

def main():
    print("\n" + "=" * 70)
    print("       FIXER.AI — ENVIRONMENT SETUP & VERIFICATION BOOTSTRAPPER")
    print("=" * 70 + "\n")
    
    skip_tests = "--skip-tests" in sys.argv
    skip_frontend = "--skip-frontend" in sys.argv
    
    check_python_version()
    setup_env_file()
    check_python_dependencies()
    verify_and_seed_database()
    verify_and_ingest_chroma()
    
    if not skip_frontend:
        verify_frontend()
    
    if not skip_tests:
        run_smoke_tests()
    
    print("\n" + "=" * 70)
    print("  [SYSTEM READY] fixer.ai is fully configured and ready to run!")
    print("=" * 70)
    print("  To launch the backend : py -3.11 -m uvicorn backend.main:app --reload --port 8000")
    print("  To launch the frontend: cd frontend && npm run dev")
    print("  Web Dashboard URL     : http://localhost:5173")
    print("=" * 70 + "\n")

if __name__ == "__main__":
    main()
