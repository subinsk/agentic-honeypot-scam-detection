"""Request and response models for the Honey-Pot API."""
from pydantic import BaseModel, Field


# --- Incoming request (per problem spec) ---

class IncomingMessage(BaseModel):
    sender: str
    text: str
    timestamp: int


class ConversationMessage(BaseModel):
    sender: str
    text: str
    timestamp: int


class RequestMetadata(BaseModel):
    channel: str | None = None
    language: str | None = None
    locale: str | None = None


class HoneyPotRequest(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    message: IncomingMessage
    conversation_history: list[ConversationMessage] = Field(default_factory=list, alias="conversationHistory")
    metadata: RequestMetadata | None = None

    model_config = {"populate_by_name": True}


# --- API response (per problem spec) ---

class AgentOutput(BaseModel):
    status: str = "success"
    reply: str


# --- GUVI callback payload (mandatory) ---

class ExtractedIntelligence(BaseModel):
    bank_accounts: list[str] = Field(default_factory=list, alias="bankAccounts")
    upi_ids: list[str] = Field(default_factory=list, alias="upiIds")
    phishing_links: list[str] = Field(default_factory=list, alias="phishingLinks")
    phone_numbers: list[str] = Field(default_factory=list, alias="phoneNumbers")
    suspicious_keywords: list[str] = Field(default_factory=list, alias="suspiciousKeywords")

    model_config = {"populate_by_name": True}


class GuviCallbackPayload(BaseModel):
    session_id: str = Field(..., alias="sessionId")
    scam_detected: bool = Field(..., alias="scamDetected")
    total_messages_exchanged: int = Field(..., alias="totalMessagesExchanged")
    extracted_intelligence: ExtractedIntelligence = Field(..., alias="extractedIntelligence")
    agent_notes: str = Field(..., alias="agentNotes")

    model_config = {"populate_by_name": True}
