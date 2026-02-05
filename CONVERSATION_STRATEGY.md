# Conversation Strategy — 20 Turns for Quick Results

## Why 20 turns?

**20 turns = ~40 total messages (20 from scammer + 20 from agent)**

This is the sweet spot for:
- ✅ **Quick results** — Test completes in ~2-3 minutes (depends on LLM speed)
- ✅ **Sufficient intelligence** — Agent extracts 3-5 UPI IDs, bank accounts, phones by turn 20
- ✅ **Realistic depth** — Real scam conversations rarely go beyond 30-40 messages
- ✅ **Hackathon scoring** — Shows multi-turn engagement without taking too long

## How the agent manages conversation length

### Turns 1-10: Active extraction
- Keep asking for alternatives when methods "don't work"
- Extract UPI → bank account → phone → more bank accounts
- Act confused but willing

### Turns 11-15: Continue but slower
- Still extract info but with slightly more hesitation
- "Let me try one more time..."
- "Can you confirm that account number again?"

### Turns 16-20: Natural wrap-up
- Once 3+ payment methods extracted, agent starts closing
- "Let me go to the bank branch to verify this"
- "I'll check with my son and get back to you"
- "I need to call the bank first, I'll message you later"

This prevents infinite loops while maximizing intelligence extraction.

## Adjusting the turn limit

```powershell
# Quick test (10 turns, ~20 messages)
python scripts\test_conversation.py --turns 10

# Default (20 turns, ~40 messages) - RECOMMENDED
python scripts\test_conversation.py

# Stress test (30 turns, ~60 messages)
python scripts\test_conversation.py --turns 30

# Max test (50 turns, ~100 messages)
python scripts\test_conversation.py --turns 50
```

## Expected extraction by turn count

| Turns | Messages | UPI IDs | Bank Accounts | Phone Numbers | Links |
|-------|----------|---------|---------------|---------------|-------|
| 5     | ~10      | 1-2     | 1             | 0-1           | 0-1   |
| 10    | ~20      | 2-3     | 2             | 1             | 1     |
| **20**| **~40**  | **3-5** | **3-4**       | **2**         | **1-2** |
| 30    | ~60      | 4-6     | 4-5           | 2-3           | 2     |

**Recommendation:** 20 turns gives the best balance of intelligence quality vs. test speed.

## For hackathon submission

When deploying for evaluation:
- The real evaluator will send 1-2 messages per session (not 40)
- Your agent is trained to extract on EVERY turn, so even 1 turn will get intel
- The 20-turn capability shows judges you can handle **deep engagement**
- But production will mostly be short (1-5 turn) conversations

## Auto-ending logic

The agent prompt includes:
> "After extracting multiple payment methods (3+ UPI/bank accounts), you can start wrapping up naturally..."

This means:
- If by turn 15-20 the agent has collected 3+ payment methods, it will naturally end
- Prevents the conversation from feeling repetitive
- Makes the honeypot behavior more realistic (real victims eventually leave or complete action)

## Callback timing

The GUVI callback is sent **on every turn** where scam is detected. So:
- Turn 1: Callback with 1 message, extracted keywords
- Turn 5: Callback with 10 messages, 1-2 UPI/bank accounts
- Turn 10: Callback with 20 messages, 2-3 UPI/bank accounts
- Turn 20: Callback with 40 messages, 3-5 UPI/bank accounts + phones + links

The evaluator sees **progressive intelligence accumulation** across the session.

## Summary

- **Default: 20 turns** (quick results, good intelligence)
- **Agent wraps up naturally** after extracting enough
- **~40 messages total** (20 scammer + 20 agent)
- **2-3 minutes** per test
- **3-5 payment methods** extracted by end

Perfect for hackathon demos and testing! 🎯
