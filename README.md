# fixer.ai ⚡
### Air-Gapped Industrial Predictive Maintenance & Multimodal AI Advisory System

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-Chroma-orange.svg)](https://www.trychroma.com)
[![Slack Bolt](https://img.shields.io/badge/Slack-Socket_Mode-4A154B.svg?logo=slack&logoColor=white)](https://api.slack.com/bolt)
[![Air--Gapped](https://img.shields.io/badge/Security-100%25_Air--Gapped_Ready-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-blue.svg)]()

---

## 🏭 Overview

**fixer.ai** is an on-premises, air-gapped predictive maintenance platform and multimodal AI diagnostic copilot engineered specifically for modern industrial shopfloors. It continuously monitors mechanical telemetry, computes ISO 10816 condition scores, estimates Remaining Useful Life (RUL) with transparent heuristic disclosure, and empowers factory technicians with an on-device AI advisor that cites OEM equipment manuals and **learns per-machine maintenance history over time**.

### Why fixer.ai?
- **🔒 100% Air-Gapped & Offline Ready**: Plant floor data, vibration spectra, and technician voice reports never leave the local OT network. Vector retrieval, embeddings, and reasoning models run fully locally with zero external API calls.
- **🧠 Two-Tier Isolated Vector Memory**:
  - **Tier 1 (Shared Model Manuals)**: Technical OEM documentation (FANUC, Haas, Conveyors, Calibration rigs) shared across machines of the same model.
  - **Tier 2 (Per-Machine Instance Memory)**: Strict cryptographic/logical isolation per physical asset ID (`tier2__M_01`, `tier2__M_02`, etc.). High-temperature grease fixes on Robot #1 never leak into or pollute the diagnostic context of Mill #2.
- **🔄 Instant Continual Learning**: Closing a work order in the web console or Slack instantly indexes the resolution card into that machine's Tier 2 brain. Querying the same symptom seconds later immediately returns the past repair history.
- **📊 Weakest-Link Prognostics (ISO 10816)**: Multi-sensor health scoring (0–100) where a critical vibration or torque anomaly triggers an alert regardless of nominal thermal signals.
- **⏱️ ISO 14224 Fleet Reliability & Financial ROI**: Automated plant availability %, MTBF (operating hours), MTTR (repair turnaround), and downtime cost avoided ($18,500/hr industrial benchmark).
- **🎙️ Live Multimodal Input**: Web Audio `MediaRecorder` microphone recording for hands-free technician voice reports + quick-select industrial defect sample photo gallery.
- **📄 Shift Handover Reports**: Instant one-click export of formal ISO 14224 shift handover and diagnostic audit documentation.
- **💬 Slack Bolt Socket Mode Integration**: Interactive Block Kit escalation cards, automated technician specialty routing, bi-directional thread syncing, and one-click "Mark Resolved" workflow.

---

## 📐 System Architecture

```
                    ┌─────────────────────────────────────────────────────────┐
                    │               AIR-GAPPED OT ENVIRONMENT                 │
                    └─────────────────────────────────────────────────────────┘
                                                 │
          ┌──────────────────────────────────────┼──────────────────────────────────────┐
          │                                      │                                      │
          ▼                                      ▼                                      ▼
   ┌──────────────┐                       ┌──────────────┐                       ┌──────────────┐
   │ M-01 FANUC   │                       │ M-02 Haas    │                       │ M-03 Conveyor│
   │ Welding Arm  │                       │ VF-2 Mill    │                       │ Drive Motor  │
   └──────┬───────┘                       └──────┬───────┘                       └──────┬───────┘
          │                                      │                                      │
          └──────────────────────────────┬───────┴──────────────────────────────────────┘
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │    Continuous Sensor Simulator (OU Physics)   │
                 │  - Ornstein-Uhlenbeck mean-reverting drift    │
                 │  - Heavy-tailed vibration spikes (Student-t)  │
                 │  - Thermal lag (Newton cooling ODE)           │
                 │  - Hidden progressive failure injection modes │
                 └───────────────────────┬───────────────────────┘
                                         │
                                         ▼
                 ┌───────────────────────────────────────────────┐
                 │                 FastAPI Core                  │
                 │  - WebSocket Telemetry Broadcast (1 Hz)       │
                 │  - Weakest-Link Health Scorer (ISO 10816)     │
                 │  - Linear Trend Extrapolation RUL Engine      │
                 │  - Recurring Fault Clustering & Leaderboard   │
                 └───────────────┬───────────────────────────────┘
                                 │
         ┌───────────────────────┴───────────────────────┐
         ▼                                               ▼
┌─────────────────────────────────┐             ┌─────────────────────────────────┐
│     Two-Tier Vector Storage     │             │    Multimodal Resolver Agent    │
│  ┌───────────────────────────┐  │             │  - Whisper Speech-to-Text       │
│  │ Tier 1: Shared Model Docs │  │◄────────────┤  - Vision Defect Analyzer       │
│  └───────────────────────────┘  │             │  - Real-time Sensor Snapshot    │
│  ┌───────────────────────────┐  │             │  - Context Fusion & Reasoning   │
│  │ Tier 2: Isolated Memory   │  │             │  - Decision Node & Escalation   │
│  │ (M-01, M-02, M-03, M-04)  │  │             └────────────────┬────────────────┘
│  └───────────────────────────┘  │                              │
└────────────────┬────────────────┘                              │
                 │ Continual Learning Feedback Loop              │
                 ▲                                               │
                 └──────────────────────────┬────────────────────┘
                                            │
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
┌───────────────────────────────┐                         ┌───────────────────────────────┐
│   Industrial Glassmorphic UI  │                         │   Slack Bolt (Socket Mode)    │
│  - Recharts Live Telemetry    │                         │  - Interactive Block Kit Cards│
│  - SVG Health Gauge           │                         │  - Technician @mention routing│
│  - Anomaly Injection Panel    │                         │  - One-Click Resolution Button│
│  - Technician Chat Console    │                         │  - Bi-directional Thread Sync │
└───────────────────────────────┘                         └───────────────────────────────┘
```

---

## 🛠️ Fleet Machinery Specifications

| Machine ID | Equipment Name | Class | Tracked Signals | Anomaly Trigger Preset |
|:---:|:---|:---|:---|:---|
| **M-01** | **FANUC ARC Mate 100iD** | 6-Axis Robotic Welder | Joint Torque (Nm), Vibration (mm/s), Temp (°C) | **Mode 1**: J2 Reducer Grease Breakdown (Exponential torque escalation) |
| **M-02** | **Haas VF-2 CNC Mill** | 3-Axis Precision Machining | Spindle Vibration (mm/s), Tool Load (A), Coolant Temp (°C) | **Mode 2**: Spindle Bearing Wear (Rising baseline + noise variance) |
| **M-03** | **Conveyor Drive Motor** | 480V Continuous Drive | Stator Current (A), Bearing Temp (°C), Vibration (mm/s) | **Mode 3**: Stator Overload & Mechanical Drag (Step current escalation) |
| **M-04** | **Torque Calibration Station** | QA Bay Metrology Bench | Calibration Drift (Nm), Ambient Temp (°C) | **AS9100 / ISO 6789**: Linear drift exceeding ±0.05 Nm QA tolerance |

---

## 💻 Tech Stack & Offline AI Architecture

### Low-Spec Laptop Dev Mode vs. Production Deployment
This repository is configured with zero-friction development on standard consumer hardware (Intel i5 12th Gen / 16GB RAM) via `LLM_STUB_MODE=true`. Real Chroma vector search runs natively, while LLM inference paths are structured as clean drop-in hooks for Ollama:

| Component | Dev Mode (`LLM_STUB_MODE=true`) | Production Deployment (`LLM_STUB_MODE=false`) |
|:---|:---|:---|
| **Embeddings** | Local ONNX MiniLM (Zero network dependencies) | `nomic-embed-text` via local Ollama |
| **Speech-to-Text** | Realistic deterministic transcript stubs | `whisper.cpp` / `faster-whisper` (Offline CPU) |
| **Vision Diagnostics** | Structured defect descriptions | `gemma3:4b` / `qwen2.5-vl` via Ollama |
| **Reasoning & Synthesis** | RAG-enriched technical diagnosis stub | `phi4-mini` (3.8B) via Ollama with JSON schema |
| **Vector Storage** | Persistent SQLite-backed ChromaDB | Persistent SQLite-backed ChromaDB |
| **Slack Connectivity** | Slack Bolt Socket Mode (Outbound WSS) | Slack Bolt Socket Mode (Outbound WSS) |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.11+** installed
- **Node.js 18+** and `npm` installed
- **Git**

### 2. Clone and Setup Environment
```bash
git clone https://github.com/your-org/fixer.ai.git
cd fixer.ai

# Copy environment variables
cp .env.example .env
```

### 3. Backend Setup
```bash
# Create and activate Python virtual environment
py -3.11 -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database and seed 4 machines, failure codes, and initial history
py backend/database/seed.py

# Ingest OEM manuals into Tier 1 and historical tickets into Tier 2 Chroma store
py scripts/ingest_manuals.py
```

### 4. Frontend Setup
```bash
cd frontend
npm install
npm run build    # Verify clean production build
npm run dev      # Starts Vite dev server at http://localhost:5173
```

### 5. Launch Backend Server
In a separate terminal:
```bash
py -3.11 -m uvicorn backend.main:app --reload --port 8000
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing & Verification

The test suite validates every layer of the system: Ornstein-Uhlenbeck stochastic mathematics, Chroma vector isolation, multimodal pipeline orchestration, prognostic health scoring, linear RUL heuristics, and Slack interactive workflows.

### Run All 68 Backend Unit Tests
```bash
py -3.11 -m pytest backend/tests/ -v
```
*Expected Result: 68 passed in ~16s.*

### Run End-to-End Demo Rehearsal Smoke Test
```bash
py -3.11 scripts/e2e_smoke_test.py
```
*Executes all 5 pitch demonstration steps programmatically against the running app.*

---

## 🎬 5-Step Pitch Demonstration Script

Follow this script to deliver a compelling live demonstration to evaluators or judges:

### Step 1: Baseline Operations (The Fleet Dashboard)
1. Open [http://localhost:5173](http://localhost:5173).
2. Point out all 4 machines operating at **100.0% nominal health**.
3. Highlight the live WebSocket heartbeat, the aggregate fleet OEE score, and the predicted service windows (`> 30 days`).

### Step 2: Inject Progressive Physical Failure
1. Click the **"⚡ Trigger Anomaly"** button in the top navigation bar.
2. Select **M-01 (FANUC ARC Mate 100iD)** and trigger **Mode 1: Reducer Grease Breakdown**.
3. Close the modal and watch M-01's health card:
   - Within seconds, torque drift triggers health degradation from `100%` → `warning` → `critical`.
   - The primary fault driver badge dynamically switches to `torque_nm`.
   - Prognostic RUL drops to actionable service window (`Within 24h`), transparently marked with its linear trend heuristic notice.

### Step 3: Multimodal AI Advisory & Manual Citations
1. Click on **M-01** to open the Machine Detail deep dive.
2. Observe live multi-signal Recharts graphs (Torque, Vibration, Temperature) showing physical drift.
3. In the right-hand **AI Copilot console**, click **"Use Simulated Audio"** and submit the report:
   > *"J2 axis motor torque spiking excessively during welding path. Noticeable grinding sound and black grease weeping."*
4. fixer.ai responds with:
   - High-severity diagnosis identifying the J2 harmonic drive reducer contamination.
   - **4 exact excerpt citations** from the official FANUC ARC Mate maintenance manual.
   - 6-step LOTO and flush procedure.
   - Automated routing to **Arjun Rao (Robotics Specialist)**.

### Step 4: Real-time Slack Escalation
1. Open your Slack workspace `#fixer-ai-escalations`.
2. Inspect the newly posted interactive **Block Kit Work Order Card**:
   - Includes urgent severity badge, diagnosis, confidence score, and `@Arjun Rao` technician mention.
   - Displays parts list (`Kyodo Yushi Molywhite RE No.00 grease`) and procedure.
   - Contains interactive buttons: `[Mark Resolved]` and `[Acknowledge Work Order]`.

### Step 5: Continual Learning & Zero-Leak Isolation
1. Click **"Mark Resolved"** in the web detail view (or in Slack).
2. Enter the technician resolution note:
   > *"Flushed contaminated black lubricant from J2 cavity. Refilled with 250cc fresh Kyodo Yushi grease. Torqued bolts to 12.5 Nm."*
3. The system marks the ticket resolved and immediately embeds the resolution into `tier2__M_01`.
4. Ask the copilot a follow-up question about J2 grinding on M-01:
   - **M-01 instantly recalls this specific resolution from its Tier 2 memory!**
5. Ask the same question about **M-02 (Haas VF-2)**:
   - **M-02 returns zero results from M-01**, proving 100% cross-machine memory isolation.

---

## 📂 Repository Structure

```
fixer.ai/
├── 00_PROJECT_OVERVIEW.md                  # High-level product requirements document
├── 01_ARCHITECTURE.md                      # Detailed technical architecture specification
├── 02_MOCK_MACHINERY_AND_SENSOR_SIMULATION.md # Physical simulation specifications
├── 03_OFFLINE_LLM_AND_TECH_STACK.md       # On-device model execution guidelines
├── 04_SLACK_INTEGRATION.md                 # Slack Bolt Socket Mode documentation
├── 05_BUILD_PLAN_6_DAYS.md                 # 6-day build execution roadmap
├── 06_RESEARCH_AND_SOURCES.md              # Engineering reference manuals & sources
├── DAY_STATUS.md                           # Daily build and testing audit log
├── requirements.txt                        # Backend dependencies
├── .env.example                            # Environment variables template
├── backend/
│   ├── main.py                             # FastAPI application entrypoint & lifespan
│   ├── config.py                           # Application settings & environment parsing
│   ├── api/
│   │   ├── admin.py                        # Anomaly trigger injection endpoints
│   │   ├── chat.py                         # Multimodal resolver agent endpoint
│   │   ├── machines.py                     # Fleet overview, health, RUL, & recurring faults
│   │   ├── tickets.py                      # Ticket lifecycle & resolution endpoint
│   │   ├── sensor_readings.py              # Historical sensor query endpoint
│   │   └── websocket.py                    # Live telemetry streaming hub
│   ├── database/
│   │   ├── models.py                       # 6 SQLAlchemy ORM schema models
│   │   └── seed.py                         # Seed data generator (machines, techs, tickets)
│   ├── health/
│   │   ├── scoring.py                      # Weakest-link condition scoring (ISO 10816)
│   │   └── rul.py                          # Trend-based linear RUL prognostic heuristic
│   ├── rag/
│   │   ├── chroma_client.py                # Two-tier Chroma persistent client
│   │   ├── ingestion.py                    # Markdown & PyMuPDF document chunkers
│   │   ├── retrieval.py                    # Tier 1/2 similarity search & context fusion
│   │   ├── recurring_faults.py             # Semantic clustering & fleet leaderboard
│   │   └── continual_learning.py           # Real-time resolution embedding loop
│   ├── resolver/
│   │   ├── pipeline.py                     # 7-step multimodal diagnostic pipeline
│   │   ├── speech.py                       # Technician audio transcription
│   │   ├── vision.py                       # Visual defect inspection analysis
│   │   ├── fusion.py                       # RAG-enriched contextual diagnosis
│   │   └── decision.py                     # Escalation rules & technician routing
│   ├── simulation/
│   │   ├── ou_process.py                   # Ornstein-Uhlenbeck stochastic mathematics
│   │   ├── machines.py                     # Per-machine signal physics configs
│   │   ├── failure_triggers.py             # Hidden failure escalation engines
│   │   └── simulator.py                    # Background 1 Hz telemetry clock
│   ├── slack_integration/
│   │   ├── bot.py                          # Bolt Socket Mode app runner
│   │   ├── escalation.py                   # Interactive Block Kit card generator
│   │   ├── resolution_handler.py           # Slack button interactive callback
│   │   └── message_handler.py              # In-thread bi-directional sync
│   └── tests/                              # 68 unit & integration tests
├── frontend/
│   ├── src/
│   │   ├── App.tsx                         # Multi-machine WebSocket connection hub
│   │   ├── types.ts                        # TypeScript model definitions
│   │   ├── index.css                       # Industrial dark glassmorphic design system
│   │   ├── components/
│   │   │   ├── Navbar.tsx                  # Header with system status beacon
│   │   │   ├── MachineCard.tsx             # Fleet overview card with SVG gauge
│   │   │   ├── MachineChatWindow.tsx       # Multimodal technician advisory console
│   │   │   └── TriggerModal.tsx            # Failure mode injection panel
│   │   └── pages/
│   │       ├── Dashboard.tsx               # Fleet operations executive overview
│   │       └── MachineDetail.tsx           # Multi-signal Recharts telemetry & deep dive
│   └── vite.config.ts                      # Vite build & proxy configuration
└── scripts/
    ├── download_manuals.py                 # Manual downloader & stager
    ├── ingest_manuals.py                   # Vector database ingestion utility
    ├── slack_smoke_test.py                 # Slack Bolt connectivity verification
    └── e2e_smoke_test.py                   # Full 5-step demo rehearsal automation
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
