from pydantic import BaseModel, Field

from models.conversation import ConversationState
from models.nlu import Intent


class ChatMessageRequest(BaseModel):
    phone: str = Field(..., min_length=8, max_length=20)
    text: str = Field(..., min_length=1, max_length=2000)


class ChatResponse(BaseModel):
    reply: str
    intents: list[Intent]
    state: ConversationState
    needs_human: bool


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "core"
    version: str = "0.1.0"
