"""Extract structured intelligence from conversation text."""
import re
from src.models import ExtractedIntelligence
from src.logging_config import get_logger

logger = get_logger("intelligence")

# Patterns (training-free)
BANK_ACCOUNT = re.compile(r"\b\d{4}[\s-]*\d{4}[\s-]*\d{4}\b")
UPI_ID = re.compile(r"[\w.\-]+@(paytm|phonepe|gpay|okaxis|okicici|ybl|axl|ibl)\b", re.I)
UPI_ALT = re.compile(r"\b[\w.\-]+@[\w.]+\b")  # broader; can filter by known UPI domains
PHONE = re.compile(r"(?:\+91|91|0)?[6-9]\d{9}\b")
URL = re.compile(r"https?://[^\s<>\"']+", re.I)
KEYWORDS = [
    "urgent", "verify", "blocked", "suspend", "OTP", "UPI", "bank account",
    "click here", "winner", "prize", "refund", "immediately", "asap",
]


def extract_intelligence_from_text(text: str) -> ExtractedIntelligence:
    """Extract bank accounts, UPI IDs, links, phone numbers, keywords from one blob."""
    bank = list({m.replace(" ", "").replace("-", "") for m in BANK_ACCOUNT.findall(text)})
    upi = list(set(UPI_ID.findall(text)))
    if not upi:
        upi = list(set(UPI_ALT.findall(text)))[:5]  # cap broad matches
    phones = list(set(PHONE.findall(text)))
    links = list(set(URL.findall(text)))
    seen = set()
    words = []
    lower = text.lower()
    for k in KEYWORDS:
        if k.lower() in lower and k.lower() not in seen:
            seen.add(k.lower())
            words.append(k)
    result = ExtractedIntelligence(
        bank_accounts=bank,
        upi_ids=upi,
        phishing_links=links,
        phone_numbers=phones,
        suspicious_keywords=words,
    )
    logger.debug(
        "intelligence_extracted",
        extra={
            "bank_count": len(bank),
            "upi_count": len(upi),
            "links_count": len(links),
            "phones_count": len(phones),
            "keywords_count": len(words),
        },
    )
    return result


def merge_intelligence(existing: ExtractedIntelligence, new: ExtractedIntelligence) -> ExtractedIntelligence:
    """Merge new extractions into existing (no duplicates)."""
    return ExtractedIntelligence(
        bank_accounts=list(dict.fromkeys(existing.bank_accounts + new.bank_accounts)),
        upi_ids=list(dict.fromkeys(existing.upi_ids + new.upi_ids)),
        phishing_links=list(dict.fromkeys(existing.phishing_links + new.phishing_links)),
        phone_numbers=list(dict.fromkeys(existing.phone_numbers + new.phone_numbers)),
        suspicious_keywords=list(dict.fromkeys(existing.suspicious_keywords + new.suspicious_keywords)),
    )
