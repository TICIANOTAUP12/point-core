from fastapi import APIRouter

from models.responses import ChatResponse, LinkGenerateRequest
from services.chat_response import build_chat_response
from services.conversation import process_message
from services.nlu_rules import parse_message
from services.whatsapp_link import build_whatsapp_url, message_for_intent

router = APIRouter(prefix="/link", tags=["link"])

DEFAULT_PHONE = "5492600000000"


@router.post("/generate", response_model=ChatResponse)
def link_generate(payload: LinkGenerateRequest) -> ChatResponse:
    phone = payload.phone or DEFAULT_PHONE

    if payload.text:
        record, nlu = process_message(phone, payload.text)
        return build_chat_response(record, nlu, payload.text)

    intent_type = payload.intent or ""
    preset = message_for_intent(intent_type)
    if preset is None:
        preset = (
            "Hola, consulto desde la web de Point Once. "
            "Quisiera recibir asesoramiento sobre el sistema de caja para mi comercio."
        )

    nlu = parse_message(preset)
    record, _ = process_message(phone, preset)
    return ChatResponse(
        reply=preset,
        whatsapp_url=build_whatsapp_url(preset),
        intents=nlu.intents,
        state=record.state,
        needs_human=False,
    )
