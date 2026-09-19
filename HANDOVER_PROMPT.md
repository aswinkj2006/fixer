# 📋 fixer.ai — New Device & Account Onboarding Protocol

When you transfer this repository to another device (e.g. via Git clone or USB/Zip) and open it in Antigravity IDE on a different account, copy and paste the message below into your first prompt to the AI assistant:

---

### 💬 Paste This Exact Prompt:

```markdown
Hello! I have transferred the 'fixer.ai' project to this machine.
Please read 'MIGRATION_AND_HANDOVER.md', 'README.md', and 'DAY_STATUS.md' to orient yourself.
The project is 100% complete through Day 7 (73/73 tests passing).
Please check my environment, verify if Ollama is available, check whether we are running in LLM_STUB_MODE or real inference, and let me know if everything is ready to run or demo!
```

---

### ⚡ What the Assistant Will Do:

1. Read [`MIGRATION_AND_HANDOVER.md`](file:///c:/Users/Aswin%20K%20J/Documents/Projects/fixer.ai/MIGRATION_AND_HANDOVER.md) for full context and architecture.
2. Check Python, virtualenv, and dependencies.
3. Check whether Ollama is installed and running (`ollama --version`).
4. Check `.env` to determine whether `LLM_STUB_MODE` is `true` (fast dev mode) or `false` (full local GPU inference mode).
5. Guide you to start the backend, frontend, and Slack bot.

---

### 🚀 Immediate Commands to Run Locally:

- **One-Step Bootstrapper**:
  ```cmd
  python scripts\bootstrap.py
  REM or double-click setup.bat
  ```

- **Run Backend**:
  ```powershell
  py -3.11 -m uvicorn backend.main:app --reload --port 8000
  ```

- **Run Frontend**:
  ```powershell
  cd frontend
  npm run dev
  ```

- **Run 5-Step Demo Verification**:
  ```powershell
  py -3.11 scripts/e2e_smoke_test.py
  ```

- **Run Test Suite**:
  ```powershell
  py -3.11 -m pytest backend/tests/ -v
  ```
