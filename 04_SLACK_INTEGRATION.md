# FixIQ — Slack Integration

## Purpose
Close the loop between "the resolver agent decides to escalate" and "a human technician actually acts on it," while capturing that conversation as fuel for the per-machine continual-learning RAG loop described in `01_ARCHITECTURE.md`.

## Framework
Use **Slack's Bolt framework with Socket Mode** (available for Python and JS) — not a raw webhook. Socket Mode means Slack connects out to the app rather than requiring a public URL, which matters for a laptop-based demo that isn't deployed anywhere.

## Flow

1. **Escalation trigger** — when the resolver agent's decision node (see `01_ARCHITECTURE.md` §5) determines a fault needs a technician, call `chat.postMessage` to a channel (or DM), tagging the assigned technician by their Slack user ID directly (`<@U12345>`, matched by specialty from the mock roster — not a generic channel post). Use Block Kit formatting so the message renders as a structured alert card: diagnosis, confidence, severity, and guided steps.

2. **Open a thread** — capture the `ts` (timestamp) of that initial message. Every subsequent reply, from either the technician or the bot, is posted using that `thread_ts`, keeping the entire incident visually contained in one Slack thread.

3. **Technician replies in-thread** — subscribe to the `message` event (`app.event('message')` in Bolt), scoped to that channel. When a reply arrives with a matching `thread_ts`, forward its text to the resolver agent as a continuation of that machine's conversation (same RAG context, same machine-scoped Tier 2 collection), then post the agent's response back into the same thread.

4. **Resolution signal — do not parse free text for this.** Add a Block Kit interactive button ("Mark Resolved" / "Escalate Further") to the thread. The "Mark Resolved" click is the clean, unambiguous trigger to close the ticket and kick off the embed-into-RAG step.

5. **Mirror to the website in real time** — write every Slack message (both directions) into the `ticket_messages` table at the point it is sent/received, tagged with `machine_id` and `thread_ts`. The machine detail page then reads from the local DB directly — do not re-fetch Slack's thread history on page load; write-through at message time is simpler and faster.

## Technician routing
Small mock roster (see `01_ARCHITECTURE.md` §2 for the `technicians` table: technician_id, name, specialty, slack_user_id). The resolver agent matches the diagnosed fault type to the technician whose specialty fits (mechanical / electrical / calibration) and mentions them directly. This targeted-mention detail is small but makes the demo feel like a real assignment system rather than a mock.

## Continual learning on resolution
When "Mark Resolved" is clicked:
1. Pull the full thread from `ticket_messages` for that ticket.
2. Chunk and embed the full conversation + final diagnosis + fix into that machine's own Tier 2 vector collection (see `01_ARCHITECTURE.md` §3), tagged with failure_code, date, and outcome.
3. This is what allows a later, similar symptom on the same machine to retrieve its own past resolution — the demonstrable "keeps learning per machine" behavior.

## Important caveat to state honestly to judges
Slack is a cloud service and this piece of the system requires internet, even though the LLM reasoning, vision, embeddings, and speech-to-text all run fully offline (see `03_OFFLINE_LLM_AND_TECH_STACK.md`). This is not a contradiction — state it plainly ("diagnosis and RAG run fully local; notification/escalation uses Slack") rather than letting judges assume the entire stack is air-gapped.

## Optional fallback
If demo-day wifi reliability is a concern, a local mock "Slack-style" thread UI can serve as backup so the demo doesn't depend on live Slack connectivity. This is a nice-to-have, not core — only build it if the 6-day schedule in `05_BUILD_PLAN_6_DAYS.md` has slack (time) for it.

## Where this fits in the build schedule
This is a Day 5 feature (see `05_BUILD_PLAN_6_DAYS.md`), building directly on the escalation/assignment logic already planned for that day — it mainly swaps "assign in a mock roster UI" for "assign + post to a Slack thread." Get the Slack app registered and a basic `postMessage` call working by Day 4 evening rather than starting cold on Day 5, since Slack app/OAuth setup can eat unplanned time.
