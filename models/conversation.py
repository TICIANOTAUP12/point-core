from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from models.nlu import SlotsGlobales

ConversationState = Literal[
    "idle",
    "clarifying_combo",
    "clarifying_contact",
    "confirming",
    "handoff",
    "closed",
]


class ConversationRecord(BaseModel):
    phone: str
    state: ConversationState = "idle"
    slots: SlotsGlobales = Field(default_factory=SlotsGlobales)
    needs_human: bool = False
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    message_count: int = 0
