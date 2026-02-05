"""
Mock Scammer API - Simulates realistic scammer behavior using local LLM.
Run this alongside your honeypot API to test multi-turn conversations.

Usage:
    python scripts/mock_scammer.py

Then in another terminal run the conversation tester:
    python scripts/test_conversation.py
"""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# Fallback scammer lines when LLM returns empty or unusable (e.g. DeepSeek-R1 reasoning-only)
FALLBACK_SCAMMER_LINES = [
    "Your account will be suspended! Send payment to UPI support123@paytm immediately!",
    "I am from the bank. Your card is blocked. Pay 2000 INR to verify: UPI taxdept@ybl or bank 123456789012.",
    "Urgent: Send payment to UPI support123@paytm immediately or account will be blocked!",
    "I already gave you the UPI ID. If that's not working use bank account 123456789012 IFSC SBIN0001234",
    "Why are you wasting time? Pay now or your account will be blocked! Call +919876543210",
    "That UPI is correct! Try again or use alternate payment to refund@ybl. Hurry!",
    "Fine, use this bank account instead: 987654321098. Account holder: Rajesh Kumar. Pay within 10 minutes!",
]

# Scammer persona - realistic Indian scam tactics
SCAMMER_PROMPT = """You are roleplaying as a scammer in India trying to trick someone into sending money. Your goal is to extract money using urgency and fake authority tactics.

SCAMMER TACTICS (use these):
1. Create urgency: "Your account will be blocked in 1 hour", "Immediate action required"
2. Fake authority: Pretend to be from bank, government, tax department, courier service
3. Provide payment details when asked: Give fake UPI IDs (e.g. support@paytm, verify@ybl), bank accounts (12 digits), phone numbers (+91xxxxxxxxxx)
4. If one payment method "doesn't work", quickly provide alternatives (show desperation to get paid)
5. Use poor grammar occasionally to seem less sophisticated
6. If they ask for IFSC, account holder name, or other details, make them up realistically
7. Keep responses short (1-3 sentences) and pushy

INTELLIGENCE TO LEAK (provide these when relevant):
- UPI IDs: support123@paytm, taxdept@ybl, courier@phonepe, refund@okicici
- Bank accounts: 123456789012, 987654321098, 456789012345
- Phone numbers: +919876543210, +918765432109
- Phishing links: bit.ly/verify-account, tinyurl.com/tax-urgent

NEVER:
- Admit you're a scammer
- Give up easily - always push for payment
- Be polite if they refuse - get more aggressive (but not abusive)

Reply as the scammer would to continue the conversation. Keep it short and pushy."""


class MockScammerRequest(BaseModel):
    user_reply: str  # What the "victim" (honeypot agent) said
    conversation_context: str = ""  # Previous messages for context


class MockScammerResponse(BaseModel):
    scammer_message: str


app = FastAPI(title="Mock Scammer API", description="Simulates realistic scammer for testing")


def _extract_scammer_text(raw: str) -> str:
    """Use final reply from LLM; strip reasoning blocks (e.g. DeepSeek-R1 think tags)."""
    if not raw or not raw.strip():
        return ""
    text = raw.strip()
    # Remove reasoning blocks (DeepSeek-R1 etc)
    text = re.sub(r"(?s)<think>.*?</think>", "", text, flags=re.IGNORECASE).strip()
    return text if text else ""


def generate_scammer_reply(user_reply: str, context: str = "") -> str:
    """Use local Ollama to generate realistic scammer response."""
    import random
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("SCAMMER_MODEL", "deepseek-r1:8b")
    messages = [{"role": "system", "content": SCAMMER_PROMPT}]
    if context:
        messages.append({"role": "assistant", "content": f"Previous conversation:\n{context}"})
    messages.append({"role": "user", "content": f"Victim said: {user_reply}\n\nRespond as the scammer:"})
    try:
        client = OpenAI(api_key="ollama", base_url=ollama_url)
        response = client.chat.completions.create(model=model, messages=messages, max_tokens=150, temperature=0.9)
        raw = (response.choices[0].message.content or "").strip()
        out = _extract_scammer_text(raw)
        if out:
            return out
        return random.choice(FALLBACK_SCAMMER_LINES)
    except Exception:
        return random.choice(FALLBACK_SCAMMER_LINES)


@app.post("/generate", response_model=MockScammerResponse)
def generate_scammer_message(req: MockScammerRequest):
    """Generate a realistic scammer reply based on victim's response."""
    scammer_msg = generate_scammer_reply(req.user_reply, req.conversation_context)
    return MockScammerResponse(scammer_message=scammer_msg)


@app.get("/health")
def health():
    return {"status": "ok", "service": "mock_scammer"}


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("Mock Scammer API starting on http://localhost:8001")
    print("=" * 60)
    print("\nMake sure Ollama is running:")
    print("  ollama serve")
    print("  ollama pull deepseek-r1:8b  (or llama3.2, llama3)")
    print("\nThen run the conversation tester:")
    print("  python scripts/test_conversation.py")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8001)
