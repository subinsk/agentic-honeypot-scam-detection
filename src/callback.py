"""Send mandatory final result to GUVI evaluation endpoint."""
import httpx
from src.models import ExtractedIntelligence
from src.config import settings
from src.logging_config import get_logger

logger = get_logger("callback")


def send_guvi_callback(
    session_id: str,
    scam_detected: bool,
    total_messages_exchanged: int,
    extracted_intelligence: ExtractedIntelligence,
    agent_notes: str,
) -> bool:
    """POST to GUVI callback URL. Returns True if request succeeded (2xx)."""
    # Build payload per spec: camelCase for all keys including nested extractedIntelligence
    intelligence_dict = extracted_intelligence.model_dump(by_alias=True, exclude_none=True)
    body = {
        "sessionId": session_id,
        "scamDetected": scam_detected,
        "totalMessagesExchanged": total_messages_exchanged,
        "extractedIntelligence": intelligence_dict,
        "agentNotes": agent_notes,
    }
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(settings.guvi_callback_url, json=body)
            ok = 200 <= r.status_code < 300
            if ok:
                logger.info(
                    "callback_sent",
                    extra={
                        "status_code": r.status_code,
                        "total_messages_exchanged": total_messages_exchanged,
                    },
                )
            else:
                logger.error(
                    "callback_failed_non_2xx",
                    extra={
                        "status_code": r.status_code,
                        "response_preview": (r.text or "")[:200],
                    },
                )
            return ok
    except Exception as e:
        logger.error(
            "callback_request_failed",
            extra={"error": str(e), "url": settings.guvi_callback_url},
            exc_info=True,
        )
        return False
