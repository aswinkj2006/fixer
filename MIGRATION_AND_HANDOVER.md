# fixer.ai — Migration, Handover & Hardware Switch Guide 🚀

> **Target Audience**: Developers, Evaluators, and incoming Antigravity AI Assistant instances taking over this repository on another laptop or account.

---

## 📌 1. Project Snapshot & Current State

- **System**: **fixer.ai** — Air-gapped industrial predictive maintenance & multimodal AI advisory platform for 4 mock industrial machines:
  - `M-01`: **FANUC ARC Mate 100iD** (6-axis robotic welding arm)
  - `M-02`: **Haas VF-2 CNC Mill** (3-axis vertical machining center)
  - `M-03`: **Conveyor Drive Motor** (480V continuous press line drive)
  - `M-04`: **Torque Calibration Station** (QA bay metrology bench)
- **Status**: **Days 1 to 6 are 100% COMPLETE & VERIFIED**.
  - **Backend Test Suite**: **68/68 unit tests passing** (`pytest backend/tests/`).
  - **E2E Smoke Test**: **100% passing** (`py scripts/e2e_smoke_test.py`).
  - **Frontend Production Build**: Compiles cleanly with 0 TypeScript/CSS errors (`npm run build`).
  - **Slack Bolt Socket Mode**: Verified with interactive Block Kit work orders and technician routing (`U0C2LRFUGSX`).
  - **Vector Memory**: Two-tier Chroma DB with real Tier 1 manual ingestion (420+ chunks) and Tier 2 isolated machine history.

---

## 📦 2. How to Transfer the Codebase to the New Laptop

### Option A: Using Git (Recommended)
If you want to push to a private Git repository (GitHub / GitLab):
```bash
# On the current laptop:
git init
git add .
git commit -m "feat: complete fixer.ai days 1-6 with full verification suite"
git remote add origin <your-private-repo-url>
git branch -M main
git push -u origin main

# On the new laptop:
git clone <your-private-repo-url>
cd fixer.ai
```

### Option B: Using USB Drive or Zip Archive
If transferring directly via USB or file transfer:
1. You can safely exclude `venv/` and `frontend/node_modules/` to make the transfer lightning fast (< 30 MB).
2. All staged equipment manuals, database models, seed scripts, and configuration templates are already preserved in `data/manuals/`, `backend/database/`, and `.env.example`.

---

## ⚡ 3. 5-Minute Zero-to-Running Setup on the New Laptop

On the new laptop, run the single self-contained bootstrapping script:

### On Windows:
```cmd
python scripts\bootstrap.py
# or simply double-click setup.bat
```

### On Linux / macOS:
```bash
chmod +x setup.sh
./setup.sh
# or python3 scripts/bootstrap.py
```

### What `bootstrap.py` Does Automatically:
1. Checks Python version (Python 3.10+ supported; Python 3.11 recommended).
2. Generates `.env` from `.env.example` if not already present.
3. Verifies and auto-installs any missing Python dependencies from `requirements.txt`.
4. Checks SQLite database (`backend/database/fixer.db`) and seeds initial machines, technicians, and history if needed.
5. Checks Chroma vector store (`data/chroma_db`) and auto-ingests Tier 1 manuals and Tier 2 tickets if needed.
6. Installs frontend packages (`npm install`) and verifies production build (`npm run build`).
7. Runs the entire 68-test backend suite and the 5-step demo rehearsal to guarantee 100% operational readiness.

---

## 💻 4. Hardware Transition: Switching to the Better Laptop with GPU

### Why Stub Mode Was Used on Dev Laptop:
During development, the project ran on an **Intel i5-12th Gen U-series laptop with 16GB RAM and integrated graphics**. To avoid slow or stalled inference on CPU, all LLM generation was placed in `LLM_STUB_MODE=true`. 
> **Important Note**: Even in stub mode, the vector database (**Chroma**), semantic embeddings, sensor physics, health scoring, RUL prognostics, and Slack Socket Mode are **100% REAL**.

### How to Enable Real Local LLMs on the Better Laptop (GPU / Apple Silicon):

#### 1. Install Ollama
Download and install Ollama from [https://ollama.ai](https://ollama.ai). Verify it is running:
```bash
ollama --version
```

#### 2. Pull the Pre-configured Production Models
Open a terminal and download the exact models fixer.ai is architected for:
```bash
# 1. Reasoning & synthesis model (compact 3.8B model with strict JSON formatting)
ollama pull phi4-mini

# 2. Multimodal vision defect inspector
ollama pull gemma3:4b

# 3. High-density industrial manual vector embeddings
ollama pull nomic-embed-text
```

#### 3. Toggle Stub Mode in `.env`
Open `.env` on the new laptop and change:
```ini
# Change from true to false:
LLM_STUB_MODE=false

# Confirm Ollama URL (default is http://localhost:11434):
OLLAMA_BASE_URL=http://localhost:11434
VISION_MODEL=gemma3:4b
REASONING_MODEL=phi4-mini
EMBEDDING_MODEL=nomic-embed-text
```

#### 4. How the Code Automatically Adapts:
- [`backend/resolver/fusion.py`](file:///c:/Users/Aswin%20K%20J/Documents/Projects/fixer.ai/backend/resolver/fusion.py): Automatically calls Ollama's `/api/generate` with `REASONING_MODEL` (`phi4-mini`) and `format: "json"`, sending the combined RAG context, sensor snapshot, and speech transcript.
- [`backend/resolver/vision.py`](file:///c:/Users/Aswin%20K%20J/Documents/Projects/fixer.ai/backend/resolver/vision.py): Automatically encodes the uploaded defect image and calls Ollama with `VISION_MODEL` (`gemma3:4b`) to extract defect type, severity, and component damage.
- [`backend/resolver/speech.py`](file:///c:/Users/Aswin%20K%20J/Documents/Projects/fixer.ai/backend/resolver/speech.py): Production path calls `faster-whisper` on local CPU/GPU (offline with zero cloud dependency).
- [`backend/rag/chroma_client.py`](file:///c:/Users/Aswin%20K%20J/Documents/Projects/fixer.ai/backend/rag/chroma_client.py): Switches embedding function from local ONNX MiniLM to `nomic-embed-text` via Ollama.

---

## 🔔 5. Slack Integration Details

- **Protocol**: Slack Bolt with Socket Mode (uses outbound WebSocket `wss://wss-primary.slack.com/link...`).
- **Network Requirement**: Requires **NO public IP**, **NO domain**, and **NO ngrok**. Works behind factory NATs or standard Wi-Fi.
- **Configured Tokens in `.env`**:
  - `SLACK_BOT_TOKEN`: `xoxb-...` (Bot user oauth token)
  - `SLACK_APP_TOKEN`: `xapp-...` (App-level token with `connections:write` scope)
  - `SLACK_ESCALATION_CHANNEL`: `C0C2R3H1VJA` (`#fixer-ai-escalations`)
  - `SLACK_TECHNICIAN_ID`: `U0C2LRFUGSX` (Verified technician user ID for `@mentions`)
- **Offline Fallback**: If internet is disabled or tokens are absent, the application logs Slack work orders gracefully to the console without crashing.

---

## 🏃 6. Running the System Live

Launch these two services in separate terminals:

### Terminal 1: Backend API & Sensor Simulator
```bash
py -3.11 -m uvicorn backend.main:app --reload --port 8000
```
- API Documentation: `http://localhost:8000/docs`
- Live WebSocket Telemetry: `ws://localhost:8000/ws/sensors/{machine_id}`

### Terminal 2: Industrial Frontend Console
```bash
cd frontend
npm run dev
```
- Dashboard URL: `http://localhost:5173`

### Terminal 3 (Optional): Slack Interactive Socket Mode Runner
```bash
py -3.11 -m backend.slack_integration.bot
```
*(Listens for interactive "Mark Resolved" button clicks in Slack)*

---

## 🎬 7. Rehearsing the 5-Step Evaluator Demo

When presenting to judges or evaluators:

1. **Step 1 (Baseline Fleet)**: Open `http://localhost:5173`. Show all 4 machines at 100% health, live sensor sparklines, and aggregate OEE.
2. **Step 2 (Inject Anomaly)**: Click `⚡ Trigger Anomaly` in the navbar. Select **M-01** (Mode 1: Reducer Grease Breakdown). Watch M-01 health drop, primary driver show `torque_nm`, and RUL calculate a linear degradation service window.
3. **Step 3 (Multimodal Copilot)**: Click into **M-01**. In the right-hand chat console, submit a report about J2 grinding noise. Show the AI advisor diagnosing harmonic drive starvation, citing **4 excerpts from the FANUC manual**, and providing a 6-step repair checklist.
4. **Step 4 (Slack Escalation)**: Show `#fixer-ai-escalations` in Slack with the interactive Block Kit work order card, `@Arjun Rao` tag, parts list, and action buttons.
5. **Step 5 (Continual Learning & Zero-Leak Memory)**: Click `Mark Resolved` in the web view or Slack. Show that M-01 **immediately learns** this repair and recalls it upon follow-up inquiry, while M-02 (Haas Mill) has **zero knowledge** of M-01's fix.

---

## 🤖 8. New Antigravity AI Assistant Onboarding Prompt

When you open this project on the new laptop in Antigravity IDE with another account, simply paste the following prompt into the chat:

```markdown
Hello! I have transferred the 'fixer.ai' project to this machine.
Please read 'MIGRATION_AND_HANDOVER.md', 'README.md', and 'DAY_STATUS.md' to orient yourself.
The project is 100% complete through Day 6 (68/68 tests passing).
Please check my environment, verify if Ollama is available, check whether we are running in LLM_STUB_MODE or real inference, and let me know if everything is ready to run or demo!
```
