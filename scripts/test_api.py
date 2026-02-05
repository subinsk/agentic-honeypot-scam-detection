"""
Test the Honey-Pot API locally. Run with venv activated from project root.

Exit code 0 = all checks passed, 1 = failure (suitable for CI).
Callback result is not returned by the API; check the server terminal for
  callback session_id=... success=True  and  POST ... updateHoneyPotFinalResult "HTTP/1.1 200 OK".
"""
import os
import sys
from pathlib import Path

# Project root on path + load .env
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import httpx
import time

BASE = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.environ.get("API_SECRET_KEY", "your-secret-api-key-change-in-production")


def main() -> int:
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}

    print("1. GET /health")
    try:
        r = httpx.get(f"{BASE}/health", timeout=None)
        r.raise_for_status()
        print("   OK:", r.json())
    except httpx.HTTPStatusError as e:
        print("   FAIL:", e)
        print("   Status:", e.response.status_code, "Body:", e.response.text)
        return
    except Exception as e:
        print("   FAIL:", e)
        print("   Make sure the server is running: python run.py or uvicorn src.main:app --host 0.0.0.0 --port 8000")
        return 1

    print("\n2. POST / (first message - scam)")
    body1 = {
        "sessionId": "test-session-001",
        "message": {
            "sender": "scammer",
            "text": "Your bank account will be blocked today. Verify immediately.",
            "timestamp": int(time.time() * 1000),
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
    }
    try:
        r = httpx.post(f"{BASE}/", json=body1, headers=headers, timeout=None)
        r.raise_for_status()
        out = r.json()
        print("   OK:", out)
        assert out.get("status") == "success"
        assert "reply" in out
        if out.get("reply"):
            print("   Reply:", out["reply"])
    except httpx.HTTPStatusError as e:
        print("   FAIL:", e)
        print("   Status:", e.response.status_code)
        print("   Body:", e.response.text)
        try:
            print("   Detail:", e.response.json())
        except Exception:
            pass
        return 1
    except Exception as e:
        print("   FAIL:", e)
        return 1

    print("\n3. POST / (follow-up - multi-turn)")
    body2 = {
        "sessionId": "test-session-001",
        "message": {
            "sender": "scammer",
            "text": "Share your UPI ID to avoid account suspension.",
            "timestamp": int(time.time() * 1000),
        },
        "conversationHistory": [
            {"sender": "scammer", "text": body1["message"]["text"], "timestamp": int(time.time() * 1000)},
            {"sender": "user", "text": out.get("reply", "Why?"), "timestamp": int(time.time() * 1000)},
        ],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
    }
    try:
        r = httpx.post(f"{BASE}/", json=body2, headers=headers, timeout=None)
        r.raise_for_status()
        out2 = r.json()
        print("   OK:", out2)
        if out2.get("reply"):
            print("   Reply:", out2["reply"])
    except httpx.HTTPStatusError as e:
        print("   FAIL:", e)
        print("   Status:", e.response.status_code)
        print("   Body:", e.response.text)
        try:
            print("   Detail:", e.response.json())
        except Exception:
            pass
        return 1
    except Exception as e:
        print("   FAIL:", e)
        return 1

    print("\n4. POST / (scam with extractable data: UPI, bank, phone, link)")
    # Mock scammer message that contains data we extract per spec (bankAccounts, upiIds, phoneNumbers, phishingLinks, suspiciousKeywords)
    body_extract = {
        "sessionId": "test-session-extract",
        "message": {
            "sender": "scammer",
            "text": "Urgent: Send payment to 1234-5678-9012 or UPI scammer@paytm. Call +919876543210 or click http://evil-phish.example.com to verify.",
            "timestamp": int(time.time() * 1000),
        },
        "conversationHistory": [],
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
    }
    try:
        r = httpx.post(f"{BASE}/", json=body_extract, headers=headers, timeout=None)
        r.raise_for_status()
        out_extract = r.json()
        print("   OK:", out_extract)
        if out_extract.get("reply"):
            print("   Reply:", out_extract["reply"][:80] + "..." if len(out_extract.get("reply", "")) > 80 else out_extract.get("reply", ""))
        print("   (Check server logs for callback_sent + extracted_intelligence_summary: bankAccounts, upiIds, etc.)")
    except httpx.HTTPStatusError as e:
        print("   FAIL:", e)
        print("   Status:", e.response.status_code)
        print("   Body:", e.response.text)
        try:
            print("   Detail:", e.response.json())
        except Exception:
            pass
        return 1
    except Exception as e:
        print("   FAIL:", e)
        return 1

    print("\n5. POST / (no scam - expect empty reply)")
    body_safe = {
        "sessionId": "test-session-002",
        "message": {"sender": "other", "text": "Hey, are we still meeting tomorrow?", "timestamp": int(time.time() * 1000)},
        "conversationHistory": [],
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
    }
    try:
        r = httpx.post(f"{BASE}/", json=body_safe, headers=headers, timeout=None)
        r.raise_for_status()
        out3 = r.json()
        print("   OK:", out3)
        assert out3.get("status") == "success" and out3.get("reply") == ""
    except httpx.HTTPStatusError as e:
        print("   FAIL:", e)
        print("   Status:", e.response.status_code)
        print("   Body:", e.response.text)
        try:
            print("   Detail:", e.response.json())
        except Exception:
            pass
        return 1
    except Exception as e:
        print("   FAIL:", e)
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
