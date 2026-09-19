# FixIQ — Architecture

## 1. Pipeline framing: ISO 13374

ISO 13374 defines six stages for a condition-monitoring/prognostics system. Map the whole system onto this — it is a real standard, not a metaphor invented for this project, and should be referenced explicitly in the pitch:

1. **Data Acquisition** — the sensor-spoofing generator (per machine, per signal type, with hidden anomaly triggers).
2. **Data Manipulation** — cleaning/windowing the raw stream (rolling averages, low-pass filtering).
3. **State Detection** — deviation from that specific machine's own historical baseline (not a generic threshold).
4. **Health Assessment** — the 0–100 health score.
5. **Prognostic Assessment** — the RUL (remaining useful life) trend-extrapolation heuristic.
6. **Advisory Generation** — the resolver agent's diagnosis, repair steps, and escalation decision.

## 2. Data model

Structured store (Postgres or SQLite is fine for a hackathon):

- **machines**: machine_id, name, model, type (robot_arm / cnc_mill / conveyor / calibration_station), install_date, baseline_ranges (per sensor, JSON)
- **sensor_readings**: machine_id, timestamp, sensor_type, value
- **tickets**: ticket_id, machine_id, opened_at, closed_at, symptom_text, image_ref, audio_transcript, diagnosis, confidence, severity, status (open/escalated/resolved), assigned_technician_id, slack_thread_ts
- **ticket_messages**: ticket_id, sender (bot/technician), text, timestamp — this is what gets mirrored from Slack AND embedded into RAG on resolution
- **technicians**: technician_id, name, specialty (mechanical/electrical/calibration), slack_user_id
- **failure_codes**: code, problem, cause, remedy — the Problem → Cause → Remedy taxonomy (a real manufacturing maintenance data governance pattern, not invented for this project)

## 3. RAG design — the core differentiator

**Two-tier retrieval, this distinction matters and must not be collapsed into one shared collection:**

- **Tier 1 — shared per machine *model*:** manual chunks (FANUC ARC Mate manuals, CNC mill manuals, etc.) — see `06_RESEARCH_AND_SOURCES.md` for the actual manual links to ingest. All machines of the same model share this collection since the manual doesn't change per unit.
- **Tier 2 — isolated per machine *instance*:** one vector collection per machine_id (e.g. `machine_M01`, `machine_M02`, `machine_M03`, `machine_M04`) holding that specific unit's own resolved ticket history. This is the "one part of the brain per machine" behavior — M-01's ticket history must never leak into M-02's retrieval, even if they are the same model.

Vector DB: Chroma or FAISS, both run fully local with no network dependency — required given the offline constraint.

**Continual learning loop:**
1. Ticket opens (from resolver agent escalation or self-resolve).
2. All messages (bot + technician, including full Slack thread) are logged to `ticket_messages`.
3. On ticket resolution (technician clicks "Mark Resolved" in Slack), the full conversation + final diagnosis + fix is chunked and embedded into that machine's own collection (Tier 2), tagged with failure_code, date, and outcome.
4. Next time that machine shows a similar symptom, retrieval against its own collection surfaces its own past fix — this is what makes "it keeps learning per machine" a demonstrable fact rather than a claim.

**Recurring fault detection:**
Cluster a machine's own past incidents (Tier 2 collection) by embedding similarity + occurrence count. Surface: "this bearing-wear pattern has occurred N times on this machine, the longest-lasting fix was X." This should visibly get more useful over the course of a demo as more tickets accumulate — a good live "look, it's learning" moment.

## 4. Health scoring & RUL (Prognostic Assessment)

- **Health score**: compare current sensor readings against that machine's own historical baseline (mean + variance over its own history), not a fleet-wide generic threshold. Score 0–100, degrading as deviation increases.
- **RUL heuristic**: fit a simple linear or exponential trend to a degrading sensor metric and extrapolate to a known failure threshold ("vibration climbing ~X%/week, hits critical in ~N days"). Label this explicitly as trend-based extrapolation in the UI — do not claim it is a trained predictive model. Judges respect honesty about scope more than an inflated ML claim.

## 5. Resolver agent flow (Advisory Generation)

1. Technician opens a machine's chat (scoped to that machine only), uploads a photo, records a voice note (e.g. "grinding noise, getting hot near the bearing").
2. **Speech-to-text**: transcribe the audio locally (see `03_OFFLINE_LLM_AND_TECH_STACK.md`).
3. **Vision step**: the local vision model produces a short structured defect description from the image (do this as a separate step, not folded into one giant multimodal call — small local models handle short, focused context much better than long noisy context).
4. **Retrieval**: query Tier 1 (shared manual for that machine's model) + Tier 2 (this machine's own past tickets) using the symptom text + defect description as the query. Also pull the current live sensor snapshot for this machine.
5. **Fusion reasoning**: a second local model call takes the short vision summary + transcript + sensor snapshot + retrieved context (kept short and pre-filtered) and outputs: ranked diagnosis with confidence, repair steps synthesized from the actual manual excerpt, and a severity flag.
6. **Decision node**:
   - High confidence + low severity → show guided self-resolve steps directly to the technician present.
   - Severity crosses threshold or requires specialized skill → auto-generate a structured work order (machine ID, fault type, parts likely needed, priority) and escalate via Slack (see `04_SLACK_INTEGRATION.md`) to the technician whose specialty matches the diagnosed fault type.

## 6. Dashboard (fleet-level)

- Fleet grid: one card per machine — health score, OEE %, next-predicted-service window, open ticket count.
- Recurring-fault leaderboard across the fleet.
- Downtime log: actual vs. predicted (becomes a genuinely interesting "look, it's tracking" chart after a few demo runs).

## 7. Machine detail view

- Live (simulated, streamed) sensor charts — vibration / temperature / torque / current time series.
- Health score gauge + RUL estimate (clearly labeled heuristic).
- Failure history table using Problem → Cause → Remedy taxonomy.
- Chat window scoped to only this machine's own memory — this is where the "separate brain per machine" behavior becomes visually obvious to a judge testing it live.

## 8. Escalation + technician roster

Small mock roster: technician_id, name, specialty (mechanical / electrical / calibration), slack_user_id. When the resolver agent escalates, it matches the diagnosed fault type to the technician with the matching specialty and mentions them directly in the Slack thread (not a generic channel post).

## 9. Sequencing risk to flag to the coding agent

Days/steps 3–5 in the build plan all depend on the sensor-spoofing generator and data model (step 1) being solid first. If time runs short, cut RUL polish before cutting the continual-learning loop or recurring-fault detection — those two are what make "learns per machine" a demonstrable fact instead of a claim in the pitch.
