"""
Interactive conversation tester - Tests your honeypot against a mock scammer.
Runs multi-turn conversations to extract maximum intelligence.

Prerequisites:
1. Honeypot API running: python run.py (port 8000)
2. Mock Scammer API running: python scripts/mock_scammer.py (port 8001)
3. Ollama running: ollama serve (for mock scammer)

Usage:
    python scripts/test_conversation.py
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import httpx
import time

HONEYPOT_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
SCAMMER_URL = "http://127.0.0.1:8001"
API_KEY = os.getenv("API_SECRET_KEY", "your-secret-api-key-change-in-production")


def test_lengthy_conversation(max_turns: int = 20):
    """Run a multi-turn conversation between mock scammer and honeypot."""
    print("=" * 80)
    print("MULTI-TURN CONVERSATION TEST")
    print("=" * 80)
    print(f"Honeypot: {HONEYPOT_URL}")
    print(f"Mock Scammer: {SCAMMER_URL}")
    print(f"Max turns: {max_turns} (auto-ends at {max_turns} for quick results)")
    print("=" * 80)
    
    # Check both services are running
    try:
        httpx.get(f"{HONEYPOT_URL}/health", timeout=None)
        httpx.get(f"{SCAMMER_URL}/health", timeout=None)
    except Exception as e:
        print(f"\n❌ ERROR: Services not running - {e}")
        print("\nStart them:")
        print("  Terminal 1: python run.py")
        print("  Terminal 2: python scripts/mock_scammer.py")
        return
    
    session_id = f"test-conversation-{int(time.time())}"
    conversation_history = []
    
    # Initial scammer message
    print("\n" + "=" * 80)
    print("TURN 1 - SCAMMER (INITIAL)")
    print("=" * 80)
    
    try:
        r = httpx.post(
            f"{SCAMMER_URL}/generate",
            json={"user_reply": "[START] You are initiating contact with a potential victim"},
            timeout=None,
        )
        scammer_msg = (r.json().get("scammer_message") or "").strip()
        if not scammer_msg:
            scammer_msg = "Your account will be blocked! Send payment to UPI support123@paytm immediately!"
            print("Scammer: (empty from API, using fallback)")
        else:
            print(f"Scammer: {scammer_msg}")
    except Exception as e:
        print(f"❌ Mock scammer failed: {e}")
        return

    # Multi-turn conversation
    for turn in range(1, max_turns + 1):
        print("\n" + "=" * 80)
        print(f"TURN {turn} - HONEYPOT")
        print("=" * 80)
        
        # Send to honeypot
        honeypot_request = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": scammer_msg,
                "timestamp": int(time.time() * 1000),
            },
            "conversationHistory": conversation_history,
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        }
        
        try:
            r = httpx.post(
                f"{HONEYPOT_URL}/",
                json=honeypot_request,
                headers={"x-api-key": API_KEY, "Content-Type": "application/json"},
                timeout=None,
            )
            r.raise_for_status()
            honeypot_response = r.json()
            agent_reply = honeypot_response.get("reply", "")
            
            if not agent_reply:
                print("❌ Honeypot returned empty reply (no scam detected)")
                break
            
            print(f"Agent: {agent_reply}")
            
            # Update conversation history
            conversation_history.append({
                "sender": "scammer",
                "text": scammer_msg,
                "timestamp": int(time.time() * 1000)
            })
            conversation_history.append({
                "sender": "user",
                "text": agent_reply,
                "timestamp": int(time.time() * 1000)
            })
            
        except httpx.HTTPError as e:
            print(f"❌ Honeypot error: {e}")
            if hasattr(e, 'response'):
                print(f"   Status: {e.response.status_code}")
                print(f"   Body: {e.response.text[:200]}")
            break
        
        # Generate next scammer message
        print("\n" + "=" * 80)
        print(f"TURN {turn + 1} - SCAMMER")
        print("=" * 80)
        
        # Build context for scammer
        context_lines = []
        for msg in conversation_history[-6:]:  # Last 6 messages for context
            sender = "Scammer" if msg["sender"] == "scammer" else "Victim"
            context_lines.append(f"{sender}: {msg['text']}")
        context = "\n".join(context_lines)
        
        try:
            r = httpx.post(
                f"{SCAMMER_URL}/generate",
                json={
                    "user_reply": agent_reply,
                    "conversation_context": context,
                },
                timeout=None,
            )
            scammer_msg = (r.json().get("scammer_message") or "").strip()
            if not scammer_msg:
                scammer_msg = "Pay now to UPI taxdept@ybl or your account will be blocked! Call +919876543210."
                print("Scammer: (empty from API, using fallback)")
            else:
                print(f"Scammer: {scammer_msg}")
        except Exception as e:
            print(f"❌ Mock scammer failed: {e}")
            break

        time.sleep(0.5)  # Brief pause between turns
    
    # Summary
    print("\n" + "=" * 80)
    print("CONVERSATION SUMMARY")
    print("=" * 80)
    print(f"Session ID: {session_id}")
    print(f"Total turns: {len(conversation_history) // 2}")
    print(f"Total messages: {len(conversation_history)}")
    print("\nCheck server logs for:")
    print("  - callback_sent with extracted_intelligence_summary")
    print("  - Bank accounts, UPI IDs, phone numbers, links extracted")
    print("=" * 80)


def test_single_turn():
    """Quick test with one scammer message."""
    print("=" * 80)
    print("SINGLE-TURN TEST")
    print("=" * 80)
    
    try:
        # Generate scammer message
        r = httpx.post(
            f"{SCAMMER_URL}/generate",
            json={"user_reply": "[START] You are contacting a potential victim about urgent account issue"},
            timeout=None,
        )
        scammer_msg = r.json()["scammer_message"]
        print(f"\nScammer: {scammer_msg}")
        
        # Send to honeypot
        r = httpx.post(
            f"{HONEYPOT_URL}/",
            json={
                "sessionId": "test-single",
                "message": {"sender": "scammer", "text": scammer_msg, "timestamp": int(time.time() * 1000)},
                "conversationHistory": [],
            },
            headers={"x-api-key": API_KEY},
            timeout=None,
        )
        agent_reply = r.json().get("reply", "")
        print(f"Agent: {agent_reply}")
        
        if not agent_reply:
            print("\n❌ No reply (scam not detected)")
        else:
            print("\n✅ Scam detected, agent engaged")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test honeypot with mock scammer")
    parser.add_argument("--turns", type=int, default=20, help="Max conversation turns (default: 20 for quick results)")
    parser.add_argument("--single", action="store_true", help="Run single-turn test only")
    args = parser.parse_args()
    
    if args.single:
        test_single_turn()
    else:
        test_lengthy_conversation(max_turns=args.turns)
