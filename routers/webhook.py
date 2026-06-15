import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, Query, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from services.chat_response import build_chat_response
from services.conversation import process_message
from services.whatsapp_client import get_whatsapp_config, is_whatsapp_send_ready, send_text_message
from services.whatsapp_link import is_api_mode

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])


def _extract_whatsapp_payload(body: dict[str, Any]) -> tuple[str, str] | None:
    """Extract phone and text from mock or Meta WhatsApp Cloud API payloads."""
    try:
        entry = body["entry"][0]
        change = entry["changes"][0]
        value = change["value"]
        message = value["messages"][0]
        phone = str(message["from"])
        text = str(message["text"]["body"])
        return phone, text
    except (KeyError, IndexError, TypeError):
        pass

    if "phone" in body and "text" in body:
        return str(body["phone"]), str(body["text"])

    return None


def _is_meta_webhook(body: dict[str, Any]) -> bool:
    return body.get("object") == "whatsapp_business_account"


def _verify_meta_signature(raw_body: bytes, signature_header: str | None) -> bool:
    app_secret = get_whatsapp_config()["app_secret"]
    if not app_secret:
        return True
    if not signature_header:
        return False

    expected = hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature_header)


@router.get("/whatsapp")
async def whatsapp_webhook_verify(
    hub_mode: str | None = Query(None, alias="hub.mode"),
    hub_verify_token: str | None = Query(None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(None, alias="hub.challenge"),
) -> Response:
    if not is_api_mode():
        logger.info("WhatsApp webhook verify ignored: WHATSAPP_MODE=link")
        return PlainTextResponse(content="Webhook disabled in link mode", status_code=404)

    verify_token = get_whatsapp_config()["verify_token"]

    if hub_mode == "subscribe" and hub_verify_token == verify_token and hub_challenge:
        logger.info("WhatsApp webhook verification succeeded")
        return PlainTextResponse(content=hub_challenge)

    logger.warning("WhatsApp webhook verification failed")
    return PlainTextResponse(content="Forbidden", status_code=403)


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request) -> Response:
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256")

    if not _verify_meta_signature(raw_body, signature):
        logger.warning("WhatsApp webhook rejected: invalid signature")
        return JSONResponse(content={"error": "invalid signature"}, status_code=403)

    try:
        body = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse(content={"error": "invalid json"}, status_code=400)

    if not isinstance(body, dict):
        return JSONResponse(content={"error": "invalid payload"}, status_code=400)

    extracted = _extract_whatsapp_payload(body)
    if extracted is None:
        if _is_meta_webhook(body):
            return JSONResponse(content={"status": "ok"})
        return JSONResponse(
            content={
                "reply": "Payload inválido. Enviá {phone, text} o formato Meta.",
                "whatsapp_url": "",
                "intents": [],
                "state": "idle",
                "needs_human": True,
            }
        )

    phone, text = extracted
    record, nlu = process_message(phone, text)
    chat_response = build_chat_response(record, nlu, text)

    if _is_meta_webhook(body):
        sent = False
        if is_whatsapp_send_ready():
            sent = await send_text_message(phone, chat_response.reply)
        return JSONResponse(
            content={
                "status": "ok",
                "sent": sent,
                "mode": "api" if is_api_mode() else "link",
                "whatsapp_url": chat_response.whatsapp_url if not sent else None,
            }
        )

    return JSONResponse(content=chat_response.model_dump(mode="json"))
