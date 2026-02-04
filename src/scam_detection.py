"""Scam intent detection: heuristics + optional LLM confirmation.

Options to make detection more comprehensive:
  1. Expanded regex patterns (below) – add more words/phrases; no external deps.
  2. External word list – set SCAM_KEYWORDS_FILE in .env to a path (one word/phrase per line);
     words are loaded at import and matched case-insensitively in addition to patterns.
  3. LLM confirmation – when an LLM is configured and heuristics flag a message,
     optionally call the LLM to confirm scam vs not (reduces false positives).
"""
import re
from pathlib import Path

from openai import OpenAI

from src.models import ConversationMessage, IncomingMessage
from src.llm_config import get_configured_providers_in_priority, has_llm_configured
from src.logging_config import get_logger
from src.config import settings

logger = get_logger("scam_detection")

# --- Option 1: Comprehensive regex patterns (training-free) ---
# Categories: account actions, verification/KYC, OTP/UPI/banking, urgency, phishing cues,
# lottery/prize, refund/cashback, impersonation/authority, generic scam terms
SCAM_PATTERNS = [
    # Account status / lock / freeze
    r"\b(blocked|suspend|suspended|freeze|frozen|deactivat(e|ed)|reactivat(e|ion))\b",
    r"\b(account\s*(block|lock|suspend|freeze)|lock(ed)?\s*account)\b",
    r"\b(verify|verification|confirm|kyc|know\s*your\s*customer)\s*(now|immediately|urgent|mandatory)?\b",
    # OTP / UPI / banking
    r"\b(OTP|one[\s.]*time[\s.]*password|one[\s.]*time[\s.]*pin)\b",
    r"\b(UPI|upi)\s*(id|link|pin|number)?\b",
    r"\b(bank\s*account|account\s*block|branch\s*name|ifsc|aadhaar|pan\s*card)\b",
    r"\b(card\s*number|cvv|pin\s*code|atm\s*pin)\b",
    r"\b(transfer\s*(money|funds)|send\s*money|pay\s*now)\b",
    # Urgency / FOMO
    r"\b(urgent|immediately|asap|right\s*now|within\s*\d+\s*(min|hour|day)|expir(e|es|ing))\b",
    r"\b(act\s*now|don't\s*delay|last\s*chance|limited\s*time)\b",
    # Phishing / links
    r"\b(click\s*(here|link|now)|link\s*below|open\s*link|secure\s*link)\b",
    r"\b(http[s]?://|bit\.ly|tinyurl|short\s*link)\b",
    r"\b(phish|malicious|fraud|scam|fake)\b",
    # Lottery / prize / reward
    r"\b(winner|won|prize|reward|lottery|jackpot)\s*(claim|click|collect)\b",
    r"\b(congratulations\s*you\s*won|you\s*have\s*won)\b",
    # Refund / cashback / too-good
    r"\b(refund|cashback|reward)\s*(link|click|claim|avail)\b",
    r"\b(free\s*gift|free\s*money|double\s*your\s*money)\b",
    # Impersonation / authority
    r"\b(income\s*tax|tax\s*department|reserve\s*bank|rbi|police\s*complaint)\b",
    r"\b(customer\s*care\s*number|helpline\s*number|call\s*this\s*number)\b",
]
COMPILED = [re.compile(p, re.I) for p in SCAM_PATTERNS]

# --- Option 2: External word list (optional) ---
# Set SCAM_KEYWORDS_FILE in .env to a path; one word/phrase per line, case-insensitive match.
def _load_extra_keywords() -> list[str]:
    path = (getattr(settings, "scam_keywords_file", None) or "").strip()
    if not path:
        return []
    p = Path(path).expanduser().resolve()
    if not p.is_file():
        logger.debug("scam_keywords_file_not_found", extra={"path": str(p)})
        return []
    lines = [ln.strip() for ln in p.read_text(encoding="utf-8", errors="ignore").splitlines() if ln.strip()]
    return lines


_EXTRA_KEYWORDS: list[str] = _load_extra_keywords()


def _heuristic_score(text: str) -> float:
    """Return 0-1 score from pattern matches + optional extra keywords."""
    if not text or not text.strip():
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for p in COMPILED if p.search(text))
    # Option 2: extra keywords from file (capped so patterns still matter)
    keyword_hits = sum(1 for kw in _EXTRA_KEYWORDS if kw and kw.lower() in text_lower)
    hits += min(2, keyword_hits)  # at most 2 extra hits from word list
    return min(1.0, hits / 3.0)  # 3+ distinct signals -> high score


def detect_scam_intent(
    message: IncomingMessage,
    conversation_history: list[ConversationMessage],
) -> tuple[bool, float]:
    """
    Detect scam intent. Returns (is_scam, confidence 0–1).
    Uses heuristics; can be extended with LLM when an LLM provider is configured.
    """
    full_text = message.text
    for m in conversation_history:
        full_text += " " + m.text

    score = _heuristic_score(full_text)
    is_scam = score >= 0.33  # threshold

    logger.debug(
        "heuristic_score_computed",
        extra={"score": round(score, 4), "is_scam": is_scam, "text_len": len(full_text)},
    )

    # Option 3: LLM confirmation when heuristics flag scam (reduces false positives)
    if has_llm_configured() and is_scam:
        if not _llm_confirm_scam(full_text):
            is_scam = False
            score = min(score, 0.25)  # lower confidence when LLM disagrees

    return is_scam, score


# --- Option 3: LLM confirmation (optional) ---
_SCAM_CONFIRM_PROMPT = """You are a scam detector. Given the message below, does it look like a scam or phishing attempt (e.g. fake urgency, request for OTP/UPI/bank details, prize/refund lure)? Reply with exactly YES or NO, nothing else."""


def _llm_confirm_scam(text: str) -> bool:
    """Ask the configured LLM if the text looks like a scam. Returns True only if LLM says YES."""
    providers = get_configured_providers_in_priority()
    if not providers:
        return True  # no LLM -> keep heuristic result
    last_error: Exception | None = None
    for provider, cfg in providers:
        try:
            client = OpenAI(api_key=cfg.api_key, base_url=cfg.base_url)
            r = client.chat.completions.create(
                model=cfg.model,
                messages=[
                    {"role": "system", "content": _SCAM_CONFIRM_PROMPT},
                    {"role": "user", "content": text[:2000]},
                ],
                max_tokens=10,
                temperature=0.0,
            )
            raw = (r.choices[0].message.content or "").strip().upper()
            if "YES" in raw:
                return True
            if "NO" in raw:
                return False
            # ambiguous reply -> treat as no confirmation
            return False
        except Exception as e:
            last_error = e
            logger.warning(
                "scam_confirm_llm_failed",
                extra={"provider": provider.value, "error": str(e)},
            )
    # all providers failed -> keep heuristic result
    logger.debug("scam_confirm_llm_all_failed", extra={"last_error": str(last_error)})
    return True
