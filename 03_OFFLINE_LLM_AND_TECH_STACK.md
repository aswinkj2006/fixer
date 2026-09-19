# FixIQ — Offline LLM & Tech Stack

## Hard constraint
Everything in the reasoning/vision/embedding/speech pipeline must run **fully offline on a local quantized model**, not a cloud API — this is intentional and central to the pitch: it proves to judges that nothing is faked or secretly calling out to a large cloud model. The one explicit, acknowledged exception is Slack, which requires internet for notifications/escalation (see `04_SLACK_INTEGRATION.md`) — this distinction should be stated honestly to judges, not hidden or blurred.

## Hardware reality check
The primary development laptop is low-spec. **Test actual inference speed on Day 1**, before committing the architecture around it — run a real image + retrieved-text inference and time it, so latency is a known, planned-for part of the demo pacing rather than a live surprise. If too slow, consider borrowing a friend's laptop — but first check what that laptop actually offers (more RAM enables a bigger model like gemma3:12b for better vision quality; a discrete GPU massively speeds up the *same* small models rather than requiring bigger ones). Decide which upgrade path based on the actual hardware available, not by default.

## Recommended local model stack (via Ollama)

- **Multimodal (vision + text) model: Gemma 3 4B** — `ollama pull gemma3:4b`. Easiest multimodal model to get running (no separate vision-projector setup headaches), ~3GB at Q4 quantization, handles both image input and text reasoning in one model. This simplifies the stack significantly given the time crunch — start here.
  - Upgrade path if better hardware becomes available: Qwen3-VL (4B or 8B) — currently the strongest small open vision-language family, ~6GB at Q4 for the 8B variant.
- **Text-only reasoning model (optional split): Phi-4-mini (3.8B)** — best reasoning-per-GB in its size class, ~2.2GB at Q4. Useful if splitting the pipeline: vision model produces a short structured defect description, then this model does the fusion reasoning over RAG + sensor data as a separate call, rather than asking one small model to do everything in a single pass.
- **Embeddings: nomic-embed-text** via Ollama — small, fast, fully local, pairs well with Chroma.
- **Speech-to-text: whisper.cpp** (tiny.en or base.en model) — runs fast on CPU, fully offline, no GPU required.

## Why decompose instead of one giant multimodal call
Small (3–4B) local models handle **short, focused context** far better than long, noisy context, and produce noticeably weaker reasoning than a large cloud model if asked to do everything in one pass. Recommended pipeline shape:

1. Vision model → short structured defect description (not the raw image forwarded downstream).
2. Retrieval → short, pre-filtered context from Tier 1 (manual) + Tier 2 (this machine's own history).
3. Reasoning model → takes the short defect description + transcript + sensor snapshot + short retrieved context → outputs diagnosis, confidence, repair steps, severity.

This keeps each individual call small and fast, which also helps with the laptop latency problem.

## Vector DB
Chroma or FAISS — both file-based/local, no network dependency, required given the offline constraint. Two collection tiers per the RAG design in `01_ARCHITECTURE.md`:
- Shared per machine *model* (manuals)
- Isolated per machine *instance* (that unit's own ticket history)

## Backend / frontend suggestions (not prescriptive — coding agent should adapt to what's fastest to build)
- Backend: FastAPI (Python) pairs naturally with Ollama's local OpenAI-compatible endpoint, Chroma, and whisper.cpp bindings.
- Structured data: SQLite is sufficient for a hackathon (machines, sensor_readings, tickets, ticket_messages, technicians, failure_codes — see `01_ARCHITECTURE.md` for schema).
- Real-time sensor streaming to frontend: WebSocket.
- Frontend: React (or any lightweight web framework) with a charting library (Recharts or similar) for the live sensor charts and dashboard.
- Work order / structured LLM output: request JSON output from the reasoning model, parse into the ticket record, render as a card in the UI.

## Notes on other model options considered (for context, not required)
- Llama 3.2 3B — fast, good tool-use for its size, text-only.
- Ministral 3 3B — vision + long context, European-language focus.
- granite4:3b — Apache 2.0 licensed enterprise-focused small model.
These are viable fallbacks if Gemma 3 4B underperforms on the specific defect-recognition task during testing — worth a quick side-by-side test on Day 1 if time allows, but Gemma 3 4B is the recommended default given ease of setup.
