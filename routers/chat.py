from fastapi import APIRouter

from models.responses import ChatMessageRequest, ChatResponse
from services.conversation import process_message
from services.responder import build_reply

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
def chat_message(payload: ChatMessageRequest) -> ChatResponse:
    record, nlu = process_message(payload.phone, payload.text)
    reply = build_reply(record, nlu)
    return ChatResponse(
        reply=reply,
        intents=nlu.intents,
        state=record.state,
        needs_human=record.needs_human,
    )
