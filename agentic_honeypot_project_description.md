# Agentic Honey-Pot for Scam Detection & Intelligence Extraction

## Executive Overview

India is witnessing a rapid rise in digital frauds driven by social engineering, urgency-based manipulation, and adaptive scam tactics across SMS, WhatsApp, email, and chat platforms. Traditional static detection systems struggle to respond effectively to these evolving threats.

This project implements an **AI-powered Agentic Honey-Pot system**, designed and built strictly in accordance with the official hackathon problem definition. The solution detects scam intent in incoming messages and autonomously engages scammers using a realistic human-like AI agent to extract actionable fraud intelligence, without revealing detection.

The system is delivered as a **stateless, secure REST API**, aligned exactly with the prescribed input/output formats, evaluation flow, and ethical constraints.

---

## Official Problem Statement (As Provided)

### Problem Statement 2  
**Agentic Honey-Pot for Scam Detection & Intelligence Extraction**

### 1. Introduction
Online scams such as bank fraud, UPI fraud, phishing, and fake offers are becoming increasingly adaptive. Scammers change their tactics based on user responses, making traditional detection systems ineffective.

This challenge requires participants to build an Agentic Honey-Pot — an AI-powered system that detects scam intent and autonomously engages scammers to extract useful intelligence without revealing detection.

### 2. Objective
Design and deploy an AI-driven honeypot system that can:
- Detect scam or fraudulent messages
- Activate an autonomous AI Agent
- Maintain a believable human-like persona
- Handle multi-turn conversations
- Extract scam-related intelligence
- Return structured results via an API

### 3. What You Need to Build
Participants must deploy a public REST API that:
- Accepts incoming message events
- Detects scam intent
- Hands control to an AI Agent
- Engages scammers autonomously
- Extracts actionable intelligence
- Returns a structured JSON response
- Secures access using an API key

### 4. API Authentication
- `x-api-key: YOUR_SECRET_API_KEY`
- `Content-Type: application/json`

### 5. Evaluation Flow
1. Platform sends a suspected scam message
2. Your system analyzes the message
3. If scam intent is detected, the AI Agent is activated
4. The Agent continues the conversation
5. Intelligence is extracted and returned
6. Performance is evaluated

### 6. API Request Format (Input)
Each API request represents one incoming message in a conversation.

#### 6.1 First Message (Start of Conversation)
This is the initial message sent by a suspected scammer. There is no prior conversation history.

```json
{
  "sessionId": "wertyu-dfghj-ertyui",
  "message": {
    "sender": "scammer",
    "text": "Your bank account will be blocked today. Verify immediately.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

#### 6.2 Second Message (Follow-Up Message)
This request represents a continuation of the same conversation. Previous messages are now included in `conversationHistory`.

```json
{
  "sessionId": "wertyu-dfghj-ertyui",
  "message": {
    "sender": "scammer",
    "text": "Share your UPI ID to avoid account suspension.",
    "timestamp": 1770005528731
  },
  "conversationHistory": [
    {
      "sender": "scammer",
      "text": "Your bank account will be blocked today. Verify immediately.",
      "timestamp": 1770005528731
    },
    {
      "sender": "user",
      "text": "Why will my account be blocked?",
      "timestamp": 1770005528731
    }
  ],
  "metadata": {
    "channel": "SMS",
    "language": "English",
    "locale": "IN"
  }
}
```

#### 6.3 Request Body Field Explanation
- **message (Required)**: Latest incoming message
- **conversationHistory (Optional)**: Empty for first message, required for follow-ups
- **metadata (Optional but Recommended)**: Channel, language, locale

### 7. Agent Behavior Expectations
The AI Agent must:
- Handle multi-turn conversations
- Adapt responses dynamically
- Avoid revealing scam detection
- Behave like a real human
- Perform self-correction if needed

### 8. Agent Output Format
```json
{
  "status": "success",
  "reply": "Why is my account being suspended?"
}
```

### 9. Evaluation Criteria
- Scam detection accuracy
- Quality of agentic engagement
- Intelligence extraction
- API stability and response time
- Ethical behavior

### 10. Constraints & Ethics
- ❌ No impersonation of real individuals
- ❌ No illegal instructions
- ❌ No harassment
- ✅ Responsible data handling

### 11. One-Line Summary
Build an AI-powered agentic honeypot API that detects scam messages, handles multi-turn conversations, and extracts scam intelligence without exposing detection.

### 12. Mandatory Final Result Callback (Very Important)
Once the system detects scam intent and the AI Agent completes the engagement, participants must send the final extracted intelligence to the GUVI evaluation endpoint. This is mandatory for evaluation.

**Callback Endpoint**  
`POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult`

**Payload Example**
```json
{
  "sessionId": "abc123-session-id",
  "scamDetected": true,
  "totalMessagesExchanged": 18,
  "extractedIntelligence": {
    "bankAccounts": ["XXXX-XXXX-XXXX"],
    "upiIds": ["scammer@upi"],
    "phishingLinks": ["http://malicious-link.example"],
    "phoneNumbers": ["+91XXXXXXXXXX"],
    "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
  },
  "agentNotes": "Scammer used urgency tactics and payment redirection"
}
```

---

## Solution Add-ons & Implementation Details

### System Architecture (Spec-Aligned)

The solution is implemented as a **stateless REST API**, strictly following the interaction model defined in the official problem statement. The system does not maintain internal databases or long-term session storage. All conversational context required for multi-turn reasoning is derived exclusively from the `conversationHistory` field provided in each incoming request.

**High-level flow:**
1. Receive incoming message event via API
2. Parse `sessionId`, `message`, and `conversationHistory`
3. Perform scam intent analysis
4. Activate agentic engagement if scam intent is detected
5. Generate human-like response
6. Extract structured intelligence from conversation
7. Trigger mandatory final callback after engagement completion

---

### Finalized Tech Stack

#### Backend & API Layer
- **FastAPI (Python)**
  - Asynchronous REST API framework
  - Strict request/response validation
  - High performance and low latency
  - Auto-generated OpenAPI documentation

#### AI & Reasoning Layer
- **Large Language Model (LLM)**
  - Used for scam intent reasoning
  - Autonomous agent response generation
  - Structured intelligence extraction

Examples of compatible LLMs:
- OpenAI GPT family
- Azure OpenAI deployments
- Open-source instruction-tuned LLMs (if permitted)

The system is model-agnostic and can switch providers without architectural changes.

#### ML Models (Training-Free)
- ❌ No supervised model training
- ❌ No custom datasets required

Instead, the system relies on:
- Prompt-driven reasoning
- Few-shot / zero-shot classification
- Pattern-based heuristics combined with LLM validation

This approach ensures faster development, easier compliance, and lower operational risk during evaluation.

---

### Core Features (Detailed)

#### 1. Scam Intent Detection Engine

The system analyzes incoming messages using a hybrid reasoning approach:
- Detection of urgency-based language ("blocked", "verify", "immediately")
- Identification of financial manipulation cues (UPI, bank, OTP)
- Contextual analysis across multiple conversation turns
- LLM-based intent confirmation to reduce false positives

Output:
- Boolean scam detection flag
- Confidence score used internally for decision-making

---

#### 2. Agent Handoff & Control Logic

Once scam intent is confirmed:
- Control is transferred from the detection module to the autonomous agent
- All subsequent responses are generated by the agent
- Scam detection is never disclosed to the sender

This handoff mechanism is a mandatory requirement and central to the evaluation criteria.

---

#### 3. Autonomous Scam Engagement Agent

The AI agent simulates a believable human persona to keep scammers engaged and extract intelligence.

Key capabilities:
- Multi-turn conversation handling using full conversation history
- Persona consistency (e.g., cautious user, confused customer)
- Adaptive questioning strategies
- Self-correction to maintain realism

The agent is explicitly designed to avoid impersonation of real individuals or institutions.

---

#### 4. Intelligence Extraction Module

During and after engagement, the system extracts structured intelligence including:
- Bank account numbers
- UPI IDs
- Phishing URLs
- Phone numbers
- Scam-related keywords and tactics

Extraction techniques:
- Pattern matching (regex-based)
- LLM-driven structured output generation

All extracted data is aggregated per session for final reporting.

---

#### 5. Mandatory Evaluation Callback Integration

After scam detection and sufficient engagement:
- The system sends a final structured payload to the GUVI evaluation endpoint
- This callback is mandatory and required for scoring

The payload includes:
- Session identifier
- Scam detection confirmation
- Total message count
- Extracted intelligence object
- Agent behavioral summary

---

### Security & Access Control

- API key-based authentication
- Validation of `x-api-key` header on every request
- Rejection of unauthorized or malformed requests

---

### Ethical & Responsible AI Design

The system strictly adheres to ethical constraints defined in the problem statement:
- No impersonation of real individuals or organizations
- No illegal or harmful instructions
- No harassment or abusive behavior
- Responsible handling of extracted scam data

Ethical safeguards are embedded directly into agent prompts and response validation.

---

### Evaluation Readiness & Compliance

The solution is designed to maximize scores across all evaluation dimensions:
- Scam detection accuracy
- Depth and quality of agentic engagement
- Completeness of extracted intelligence
- API stability and reliability
- Full adherence to official specifications

---

## Conclusion

This project delivers a robust, fully compliant Agentic Honey-Pot system that transforms scam detection into proactive intelligence extraction. By combining stateless API design, agentic AI behavior, and structured reporting, the solution demonstrates practical readiness for real-world fraud mitigation while aligning strongly with the goals of the India AI Impact Buildathon.

