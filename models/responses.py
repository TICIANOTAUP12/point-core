from pydantic import BaseModel, Field, model_validator

from models.conversation import ConversationState
from models.nlu import Intent


class ChatMessageRequest(BaseModel):
    phone: str = Field(..., min_length=8, max_length=20)
    text: str = Field(..., min_length=1, max_length=2000)


class LinkGenerateRequest(BaseModel):
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    text: str | None = Field(default=None, min_length=1, max_length=2000)
    intent: str | None = Field(default=None, min_length=1, max_length=64)

    @model_validator(mode="after")
    def require_text_or_intent(self) -> "LinkGenerateRequest":
        if not self.text and not self.intent:
            raise ValueError("Se requiere text o intent")
        return self


class ChatResponse(BaseModel):
    reply: str
    whatsapp_url: str
    intents: list[Intent]
    state: ConversationState
    needs_human: bool


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "core"
    version: str = "0.1.0"
