from typing import Any

from fastapi import APIRouter, Request

from models.responses import ChatMessageRequest, ChatResponse
from services.conversation import process_message
from services.responder import build_reply

router = APIRouter(prefix="/webhook", tags=["webhook"])


def _extract_whatsapp_payload(body: dict[str, Any]) -> tuple[str, str] | None:
    """Mock Meta WhatsApp Cloud API shape."""
    try:
        entry = body["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        message = value["messages"][0]
        phone = message["from"]
        text = message["text"]["body"]
        return phone, text
    except (KeyError, IndexError, TypeError):
        pass

    if "phone" in body and "text" in body:
        return str(body["phone"]), str(body["text"])

    return None


@router.post("/whatsapp", response_model=ChatResponse)
async def whatsapp_webhook(request: Request) -> ChatResponse:
    body = await request.json()
    extracted = _extract_whatsapp_payload(body)
    if extracted is None:
        return ChatResponse(
            reply="Payload inválido. Enviá {phone, text} o formato Meta mock.",
            intents=[],
            state="idle",
            needs_human=True,
        )

    phone, text = extracted
    record, nlu = process_message(phone, text)
    reply = build_reply(record, nlu)
    return ChatResponse(
        reply=reply,
        intents=nlu.intents,
        state=record.state,
        needs_human=record.needs_human,
    )
