from models.conversation import ConversationRecord
from models.nlu import NluResult
from models.responses import ChatResponse
from services.responder import build_reply
from services.whatsapp_link import build_consumer_message, build_whatsapp_url


def build_chat_response(
    record: ConversationRecord,
    nlu: NluResult,
    user_text: str,
) -> ChatResponse:
    reply = build_reply(record, nlu)
    wa_message = build_consumer_message(user_text, nlu, record.needs_human or nlu.needs_human)
    return ChatResponse(
        reply=reply,
        whatsapp_url=build_whatsapp_url(wa_message),
        intents=nlu.intents,
        state=record.state,
        needs_human=record.needs_human or nlu.needs_human,
    )
