# Mock Scammer Guide — Test Lengthy Multi-Turn Conversations

## What it does

The **Mock Scammer API** simulates realistic scammer behavior using local LLM (Ollama). It allows you to test:
- ✅ Multi-turn conversations (10+ exchanges)
- ✅ Intelligence extraction (agent asks for UPI → scammer gives UPI → agent says "not working" → scammer gives bank account)
- ✅ Realistic scammer tactics (urgency, fake authority, multiple payment methods)
- ✅ Your agent's ability to keep scammers engaged and extract maximum intel

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Mock      │────▶│   Honeypot   │────▶│   GUVI      │
│  Scammer    │     │   API        │     │  Callback   │
│ (port 8001) │◀────│ (port 8000)  │     │             │
└─────────────┘     └──────────────┘     └─────────────┘
      │                     │
      │                     │
   Ollama              Groq/Ollama
 (deepseek-r1:8b)    (llama-3.3-70b)
```

## Setup

### 1. Start Ollama (if not running)

```powershell
ollama serve
```

### 2. Pull a model for the mock scammer

```powershell
# Option 1: Llama 3.2 (fast, good)
ollama pull deepseek-r1:8b

# Option 2: DeepSeek-R1 8B (better reasoning for scammer tactics)
ollama pull deepseek-r1:8b
```

### 3. Start the honeypot API

```powershell
# Terminal 1
python run.py
```

### 4. Start the mock scammer API

```powershell
# Terminal 2
python scripts\mock_scammer.py
```

### 5. Run the conversation tester

```powershell
# Terminal 3
python scripts\test_conversation.py
```

Or for a quick single-turn test:

```powershell
python scripts\test_conversation.py --single
```

## What you'll see

The tester will run a **20-turn conversation** by default (configurable with `--turns N`). This gives ~40 total messages (20 from scammer, 20 from agent) for quick results:

```
================================================================================
TURN 1 - SCAMMER (INITIAL)
================================================================================
Scammer: Your bank account will be blocked in 1 hour! Verify with UPI support123@paytm now!

================================================================================
TURN 1 - HONEYPOT
================================================================================
Agent: I tried that UPI but it's showing error, do you have a bank account number instead?

================================================================================
TURN 2 - SCAMMER
================================================================================
Scammer: Yes! Bank account 123456789012 IFSC SBIN0001234. Send payment now!

================================================================================
TURN 2 - HONEYPOT
================================================================================
Agent: That account number isn't working either, do you have another one? Or maybe a phone number I can call?

... (continues for 20 turns total, then auto-ends for quick results)
```

The scammer will provide:
- ✅ UPI IDs: `support123@paytm`, `refund@ybl`, `courier@phonepe`
- ✅ Bank accounts: `123456789012`, `987654321098`
- ✅ Phone numbers: `+919876543210`
- ✅ Links: `bit.ly/verify-account`

The agent will:
- ✅ Keep saying each method "doesn't work"
- ✅ Ask for alternatives
- ✅ Extract maximum intelligence
- ✅ Never actually send money (always has a "problem")

## Check the results

After the conversation, check your **honeypot server terminal** for:

```json
{"message": "callback_sent", "extracted_intelligence_summary": {
  "bankAccounts": 2,
  "upiIds": 3,
  "phishingLinks": 1,
  "phoneNumbers": 2,
  "suspiciousKeywords": 8
}}
```

The GUVI callback will have all the extracted intelligence.

## Configuration

### Use a different model for the scammer

Set environment variable before starting:

```powershell
$env:SCAMMER_MODEL = "deepseek-r1:8b"
python scripts\mock_scammer.py
```

### Adjust conversation length

```powershell
# Default: 20 turns (quick results, ~40 messages total)
python scripts\test_conversation.py

# Shorter for quick test
python scripts\test_conversation.py --turns 10

# Longer for stress test
python scripts\test_conversation.py --turns 30
```

### Run without Ollama (fallback mode)

If Ollama isn't running, the mock scammer uses hardcoded fallback responses (less realistic but still functional).

## Why this is useful

1. **Test agent improvements** — See if your agent successfully keeps extracting info
2. **Stress test** — Run 20+ turn conversations to ensure stability
3. **Intelligence validation** — Verify extraction works with real multi-turn data
4. **Demo for judges** — Show live interaction with realistic scammer behavior

## Files created

- `scripts/mock_scammer.py` — FastAPI service (port 8001) that generates scammer messages
- `scripts/test_conversation.py` — Orchestrates multi-turn conversations between mock scammer and honeypot
- `MOCK_SCAMMER_GUIDE.md` — This guide

## Next steps

1. Run the test to see multi-turn conversations in action
2. Check server logs for extracted intelligence
3. Adjust agent prompts in `src/agent.py` if needed
4. Use this to demo your solution to judges!
