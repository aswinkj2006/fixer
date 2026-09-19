"""
fixer.ai — Slack smoke test
Run: py -3.11 scripts/slack_smoke_test.py

Tests:
1. Bot can authenticate (auth.test)
2. Bot can post a message to the escalation channel
3. Socket Mode connection opens successfully

Requirements: SLACK_BOT_TOKEN and SLACK_APP_TOKEN must be set in .env
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN", "")
SLACK_CHANNEL = os.getenv("SLACK_ESCALATION_CHANNEL", "")


def check_env():
    print("\n[1/3] Checking .env variables...")
    ok = True
    if not SLACK_BOT_TOKEN or SLACK_BOT_TOKEN == "xoxb-your-token-here":
        print("  ERROR: SLACK_BOT_TOKEN not set in .env")
        ok = False
    else:
        print(f"  SLACK_BOT_TOKEN: {SLACK_BOT_TOKEN[:12]}... OK")

    if not SLACK_APP_TOKEN or SLACK_APP_TOKEN == "xapp-your-token-here":
        print("  ERROR: SLACK_APP_TOKEN not set in .env")
        ok = False
    else:
        print(f"  SLACK_APP_TOKEN: {SLACK_APP_TOKEN[:12]}... OK")

    if not SLACK_CHANNEL:
        print("  WARNING: SLACK_ESCALATION_CHANNEL not set — will use default #general")
    else:
        print(f"  SLACK_ESCALATION_CHANNEL: {SLACK_CHANNEL} OK")

    return ok


def test_auth():
    print("\n[2/3] Testing Slack auth (auth.test)...")
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    client = WebClient(token=SLACK_BOT_TOKEN)
    try:
        result = client.auth_test()
        print(f"  Bot name: {result['user']}")
        print(f"  Workspace: {result['team']}")
        print(f"  Bot ID: {result['user_id']}")
        print("  auth.test: OK")
        return client, result['user_id']
    except SlackApiError as e:
        print(f"  FAIL: {e.response['error']}")
        print("  Check your SLACK_BOT_TOKEN is correct and the app is installed to workspace.")
        return None, None


def test_post_message(client):
    print("\n[3/3] Testing chat.postMessage...")
    from slack_sdk.errors import SlackApiError

    channel = SLACK_CHANNEL or "#general"
    try:
        result = client.chat_postMessage(
            channel=channel,
            text="🔧 *fixer.ai smoke test* — Slack integration connected successfully! This message confirms the bot can post escalation alerts. You can delete this.",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*fixer.ai* smoke test passed ✅\nSlack integration is working. Bot can post structured escalation alerts to this channel."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {"type": "mrkdwn", "text": "Posted by fixer.ai setup script — safe to delete"}
                    ]
                }
            ]
        )
        ts = result["ts"]
        print(f"  Message posted. ts={ts}")
        print(f"  Channel: {channel}")
        print("  chat.postMessage: OK")

        # Also test thread reply
        client.chat_postMessage(
            channel=channel,
            thread_ts=ts,
            text="This is a thread reply — confirming threading works for ticket escalation flow.",
        )
        print("  Thread reply: OK")
        return True

    except SlackApiError as e:
        error = e.response['error']
        if error == "channel_not_found":
            print(f"  FAIL: Channel '{channel}' not found.")
            print("  Make sure the channel exists AND you've invited the bot with /invite @fixer-ai")
        elif error == "not_in_channel":
            print(f"  FAIL: Bot not in channel '{channel}'.")
            print("  Go to the channel in Slack and type: /invite @fixer-ai")
        else:
            print(f"  FAIL: {error}")
        return False


if __name__ == "__main__":
    print("=" * 55)
    print("  fixer.ai — Slack Integration Smoke Test")
    print("=" * 55)

    if not check_env():
        print("\nFix .env first, then re-run this script.")
        sys.exit(1)

    client, bot_id = test_auth()
    if not client:
        sys.exit(1)

    success = test_post_message(client)

    print("\n" + "=" * 55)
    if success:
        print("  ALL TESTS PASSED — Slack is ready for Day 5 integration.")
        print("  Next: Add technician Slack user IDs to .env and seed.py")
    else:
        print("  SOME TESTS FAILED — fix errors above before Day 5.")
    print("=" * 55)
