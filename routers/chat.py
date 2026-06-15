from fastapi import APIRouter

from models.responses import ChatMessageRequest, ChatResponse, LinkGenerateRequest
from services.chat_response import build_chat_response
from services.conversation import process_message
from services.whatsapp_link import build_whatsapp_url, message_for_intent

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/message", response_model=ChatResponse)
def chat_message(payload: ChatMessageRequest) -> ChatResponse:
    record, nlu = process_message(payload.phone, payload.text)
    return build_chat_response(record, nlu, payload.text)
