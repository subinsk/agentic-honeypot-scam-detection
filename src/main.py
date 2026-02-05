"""Agentic Honey-Pot REST API: scam detection, agent reply, intelligence, callback."""
import uuid

from fastapi import FastAPI, Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import settings
from src.logging_config import setup_logging, get_logger, set_request_context, clear_request_context
from src.models import HoneyPotRequest, AgentOutput, IncomingMessage, ConversationMessage
from src.scam_detection import detect_scam_intent
from src.agent import generate_agent_reply, generate_agent_notes, AgentError
from src.intelligence import extract_intelligence_from_text, merge_intelligence, ExtractedIntelligence
from src.callback import send_guvi_callback

setup_logging()
logger = get_logger("main")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Set request_id (and optionally session_id) in logging context for the request lifecycle."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        set_request_context(request_id=request_id)
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            return response
        finally:
            clear_request_context()


def verify_api_key(request: Request) -> None:
    key = request.headers.get("x-api-key")
    if not key or key != settings.api_secret_key:
        logger.warning("auth_failed", extra={"reason": "invalid_or_missing_api_key"})
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


app = FastAPI(
    title="Agentic Honey-Pot for Scam Detection",
    description="Detects scam intent, engages with human-like agent, extracts intelligence.",
    version="1.0.0",
)
app.add_middleware(RequestContextMiddleware)


@app.post(
    "/",
    response_model=AgentOutput,
    dependencies=[Depends(verify_api_key)],
    responses={401: {"description": "Invalid or missing x-api-key"}},
)
def honeypot(req: HoneyPotRequest) -> AgentOutput:
    """
    Accept one incoming message. If scam intent is detected, the AI agent replies
    and extracted intelligence is sent to the evaluation callback.
    """
    set_request_context(session_id=req.session_id)
    message = req.message
    history = req.conversation_history

    logger.info(
        "request_received",
        extra={"message_len": len(message.text), "history_len": len(history)},
    )

    is_scam, confidence = detect_scam_intent(message, history)
    logger.info(
        "scam_detection_complete",
        extra={"is_scam": is_scam, "confidence": round(confidence, 4)},
    )

    if not is_scam:
        logger.info("no_scam_returning_empty_reply")
        return AgentOutput(status="success", reply="")

    try:
        reply = generate_agent_reply(message, history)
        logger.info("agent_reply_generated", extra={"reply_len": len(reply)})
    except AgentError as e:
        logger.error("agent_error", extra={"error": str(e)}, exc_info=True)
        raise HTTPException(status_code=503, detail=str(e))

    # Build full conversation text for extraction (scammer + user messages)
    full_text = message.text
    for m in history:
        full_text += " " + m.text
    extracted = extract_intelligence_from_text(full_text)

    total_messages = len(history) + 1  # current message

    # LLM-generated summary of scammer behavior for callback
    agent_notes = generate_agent_notes(message, history, extracted)

    # Mandatory callback when scam detected and agent has engaged
    callback_ok = send_guvi_callback(
        session_id=req.session_id,
        scam_detected=True,
        total_messages_exchanged=total_messages,
        extracted_intelligence=extracted,
        agent_notes=agent_notes,
    )
    logger.info(
        "callback_complete",
        extra={"total_messages": total_messages, "callback_success": callback_ok},
    )

    return AgentOutput(status="success", reply=reply)


@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "ok"}


@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}
