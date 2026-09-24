# 🤖 Fixer.ai — Agent & Team Sync Log

> **Single Source of Truth** for concurrent development between:
> - **Backend Developer**: Aswin (`backend/`, `data/`, `scripts/`)
> - **Frontend Developer**: Team Partner (`frontend/`)
> - **AI Agents**: Reads this file to understand active context, avoid touching the other person's folders, and preserve API contracts.

---

## 👥 Team Roles & Folder Ownership

```
fixer.ai/
├── backend/          <-- 🔒 OWNED BY BACKEND (Aswin). Do NOT touch from frontend branch.
├── data/             <-- 🔒 OWNED BY BACKEND (Manuals, ChromaDB, Seed data)
├── scripts/          <-- 🔒 OWNED BY BACKEND (Bootstrap, Ingestion, Tests)
├── frontend/         <-- 🎨 OWNED BY FRONTEND (Partner). Do NOT touch from backend branch.
│   ├── src/
│   │   ├── pages/        (Dashboard, MachineDetail, SimulationControl)
│   │   ├── components/   (Machine3DViewer, Navbar, MachineChatWindow, etc.)
│   │   ├── three/        (Three.js PBR materials & compound geometries)
│   │   └── types.ts      (TypeScript interfaces)
└── AGENT_SYNC.md     <-- 🔄 SHARED HANDOVER LOG (Updated on every commit)
```

---

## 🎯 Core Project Concept (In Plain English)

**Fixer.ai: The Continuously Learning RAG Technician for Industrial Machines**
- **The Problem**: Factories lose **₹18 Lakhs / minute** when lines freeze. Traditional ML models have no memory of a machine's quirks, repairs, or history.
- **The Core Idea**: A dedicated "digital doctor" for every machine with **isolated per-machine memory**. It learns each machine individually, understands wear trends, diagnoses failures via CCTV + sensors + manuals, and gets smarter every time a technician confirms a fix.
- **Architecture**:
  - **RAG (The Brain)**: Isolated per machine. Stores machine-specific sensor history, OEM manuals, repair logs, past diagnoses, and CCTV observations.
  - **LLM (The Body)**: Single shared reasoning engine. Zero retraining per machine.

### The Two Workflows:
1. **Side A (Plant Overseer)**:
   - Fleet Dashboard → Chatbot Q&A → Custom on-demand analysis charts.
2. **Side B (Machine & Technician)**:
   - Sensors & 3D CCTV Monitoring → Anomaly Diagnosis (Manuals + Past Fixes) → Tiered Alert & Repair Notes → Technician Feedback (Reward / Error signal) → RAG Brain updates.

---

## 🔌 Frozen API Contracts (Frontend-Backend Guardrail)

Frontend developer can freely simplify UI, restyle, move components, or redesign layouts **as long as these contracts remain intact**:

### 1. Fleet Status (`GET http://localhost:8000/api/fleet/status`)
```json
{
  "plant_health_score": 100.0,
  "financial_downtime_avoided_inr": 1850000.0,
  "oee_percentage": 93.8,
  "machines": [
    {
      "id": "M-01",
      "name": "FANUC ARC Mate 100iD — Welding Cell A",
      "model": "fanuc_arc_mate_100id",
      "status": "OPERATIONAL",
      "health_score": 100.0,
      "rul_hours": 720.0,
      "sensors": { "torque_nm": 18.2, "vibration_rms": 1.05 }
    }
  ]
}
```

### 2. Live WebSocket Telemetry (`ws://localhost:8000/ws/telemetry`)
Emits 1 Hz continuous sensor ticks:
```json
{
  "timestamp": "2026-09-24T14:00:00Z",
  "machine_id": "M-01",
  "status": "OPERATIONAL",
  "sensors": {
    "torque_nm": 18.4,
    "vibration_rms": 1.08,
    "weld_current_a": 180.2
  },
  "health_score": 100.0,
  "rul_hours": 720.0
}
```

### 3. Chat / Diagnostic Copilot (`POST http://localhost:8000/api/chat`)
- **Request**:
  ```json
  {
    "machine_id": "M-01",
    "query": "Joint 2 torque is spiking, what should I do?",
    "image_b64": null,
    "audio": null
  }
  ```
- **Response**:
  ```json
  {
    "response": "Flush Harmonic Drive reducer with Mobilux EP2 grease and torque flange bolts to 85 Nm.",
    "citations": ["FANUC B-83284EN/04 Section 3.2.1"],
    "confidence_score": 0.94,
    "is_bootstrapping": false
  }
  ```

### 4. Continuous Learning Feedback Loop (`POST http://localhost:8000/api/feedback`)
- **Request**:
  ```json
  {
    "machine_id": "M-01",
    "incident_id": "INC-001",
    "verified": true,
    "correction_note": "Optional note if verified is false"
  }
  ```
- **Action**: Backend immediately logs a reward (+1) or error (-1) signal and embeds the outcome into `tier2__M_01` ChromaDB collection.

---

## 📝 Live Handover & Changelog

### 🕒 Update 1: 2026-09-24 14:15
- **Author**: Backend (Aswin) & System
- **Branch**: `main`
- **What was done**:
  - Removed all obsolete/legacy `.md` docs and setup scripts.
  - Retained clean codebase: `backend/`, `frontend/`, `data/manuals/`, `scripts/`.
  - Set up `AGENT_SYNC.md` as the official contract and sync file.
  - Created dedicated branches: `feat/backend-rag` for Aswin and `feat/frontend-ui` for Frontend Partner.
- **Context for Frontend Partner**:
  - You can run frontend independently with `npm run dev`.
  - If you want to simplify pages, feel free to modify `Dashboard.tsx` and `MachineDetail.tsx`.
  - Keep sensor prop names identical to `types.ts` so WebSocket data flows seamlessly!
- **Next Steps for Backend**:
  - Expand `/api/feedback` endpoint for explicit reward/error signals and expose bootstrap confidence status.
