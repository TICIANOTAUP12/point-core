import logging
import os
from typing import Any

import httpx

from services.whatsapp_link import get_whatsapp_mode, is_api_mode

logger = logging.getLogger(__name__)

GRAPH_API_VERSION = "v21.0"
GRAPH_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def get_whatsapp_config() -> dict[str, str]:
    return {
        "token": os.getenv("WHATSAPP_TOKEN", "").strip(),
        "phone_number_id": os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip(),
        "business_account_id": os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", "").strip(),
        "verify_token": os.getenv("WEBHOOK_VERIFY_TOKEN", "").strip(),
        "app_secret": os.getenv("WHATSAPP_APP_SECRET", "").strip(),
    }


def whatsapp_connection_status() -> dict[str, Any]:
    mode = get_whatsapp_mode()
    config = get_whatsapp_config()
    display_phone = os.getenv("WHATSAPP_PHONE", "+54 264 628-1854")

    if mode == "link":
        return {
            "mode": "link",
            "configured": True,
            "missing": [],
            "signature_validation": False,
            "business_account_configured": False,
            "display_phone": display_phone,
            "integration": "wa.me redirect — el consumidor cierra la conversación en WhatsApp",
            "webhook_url": None,
            "api_enabled": False,
        }

    required = {
        "WHATSAPP_TOKEN": config["token"],
        "WHATSAPP_PHONE_NUMBER_ID": config["phone_number_id"],
        "WEBHOOK_VERIFY_TOKEN": config["verify_token"],
    }
    missing = [name for name, value in required.items() if not value]
    return {
        "mode": "api",
        "configured": not missing,
        "missing": missing,
        "signature_validation": bool(config["app_secret"]),
        "business_account_configured": bool(config["business_account_id"]),
        "display_phone": display_phone,
        "integration": "WhatsApp Cloud API — envío automático vía Graph API",
        "webhook_url": "https://sistemataup.online/api/core/webhook/whatsapp",
        "api_enabled": True,
    }


def is_whatsapp_send_ready() -> bool:
    if not is_api_mode():
        return False
    config = get_whatsapp_config()
    return bool(config["token"] and config["phone_number_id"])


async def send_text_message(to: str, text: str) -> bool:
    if not is_api_mode():
        logger.info("WhatsApp send skipped: WHATSAPP_MODE=link (use whatsapp_url redirect)")
        return False

    config = get_whatsapp_config()
    token = config["token"]
    phone_number_id = config["phone_number_id"]

    if not token or not phone_number_id:
        logger.warning("WhatsApp send skipped: missing WHATSAPP_TOKEN or WHATSAPP_PHONE_NUMBER_ID")
        return False

    url = f"{GRAPH_BASE_URL}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                json=payload,
                headers={"Authorization": f"Bearer {token}"},
            )
    except httpx.HTTPError as exc:
        logger.error("WhatsApp API request failed for recipient ending %s: %s", to[-4:], exc)
        return False

    if response.is_success:
        logger.info("WhatsApp message sent to recipient ending %s", to[-4:])
        return True

    logger.error(
        "WhatsApp API error status=%s for recipient ending %s",
        response.status_code,
        to[-4:],
    )
    return False
