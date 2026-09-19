"""
fixer.ai — Slack Bolt Socket Mode Bot Runner
Spec: 04_SLACK_INTEGRATION.md §Framework & §Flow

Wires Slack Bolt App with Socket Mode:
- Handles 'mark_resolved' and 'acknowledge_ticket' button actions
- Handles in-thread messages with two-way sync to ticket_messages
- Operates via Socket Mode (no public URL/ngrok required)
"""
import os
import asyncio
from typing import Optional

from backend.config import SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_ESCALATION_CHANNEL
from backend.slack_integration.resolution_handler import handle_slack_resolution
from backend.slack_integration.message_handler import handle_in_thread_message


def create_slack_app():
    """Builds configured Slack Bolt App instance with all action and event listeners."""
    if not SLACK_BOT_TOKEN:
        return None

    try:
        from slack_bolt import App
        from slack_bolt.adapter.socket_mode import SocketModeHandler

        app = App(token=SLACK_BOT_TOKEN)

        @app.action("mark_resolved")
        def on_mark_resolved(ack, body, client):
            ack()
            ticket_id = body["actions"][0]["value"]
            user_id = body["user"]["id"]
            user_name = body["user"].get("name")
            channel_id = body.get("channel", {}).get("id")
            thread_ts = body.get("container", {}).get("thread_ts") or body.get("message", {}).get("ts")

            # Run async resolution handler in event loop
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loop.run_until_complete(
                handle_slack_resolution(
                    ticket_id=ticket_id,
                    user_id=user_id,
                    user_name=user_name,
                    channel_id=channel_id,
                    thread_ts=thread_ts,
                    slack_client=client,
                )
            )

        @app.action("acknowledge_ticket")
        def on_acknowledge(ack, body, client):
            ack()
            user_id = body["user"]["id"]
            ticket_id = body["actions"][0]["value"]
            channel_id = body.get("channel", {}).get("id")
            thread_ts = body.get("container", {}).get("thread_ts") or body.get("message", {}).get("ts")

            if channel_id and thread_ts:
                client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=f"👀 Incident acknowledged by <@{user_id}>. Reviewing diagnostics.",
                    mrkdwn=True,
                )

        @app.action("open_machine_url")
        def on_open_machine_url(ack):
            ack()

        @app.event("message")
        def on_thread_message(event, client):
            # Only process user replies inside an escalated thread (not bot's own messages)
            thread_ts = event.get("thread_ts")
            text = event.get("text", "")
            bot_id = event.get("bot_id")
            user_id = event.get("user")

            if not thread_ts or bot_id or not user_id or not text:
                return

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loop.run_until_complete(
                handle_in_thread_message(
                    thread_ts=thread_ts,
                    text=text,
                    user_id=user_id,
                    channel_id=event.get("channel"),
                    message_ts=event.get("ts"),
                    slack_client=client,
                )
            )

        return app

    except Exception as e:
        print(f"[slack_bot] Failed to initialize Bolt app: {e}")
        return None


def run_socket_mode_bot():
    """Runs Slack Bolt in Socket Mode (call from background thread/task)."""
    if not SLACK_BOT_TOKEN or not SLACK_APP_TOKEN:
        print("[slack_bot] SLACK_BOT_TOKEN or SLACK_APP_TOKEN not provided — Socket Mode runner disabled.")
        return

    app = create_slack_app()
    if not app:
        return

    try:
        from slack_bolt.adapter.socket_mode import SocketModeHandler
        handler = SocketModeHandler(app, SLACK_APP_TOKEN)
        print("[slack_bot] Starting Bolt Socket Mode listener...")
        handler.start()
    except Exception as e:
        print(f"[slack_bot] Socket Mode handler stopped: {e}")
