import logging
import os
from typing import Any

import httpx

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
    config = get_whatsapp_config()
    required = {
        "WHATSAPP_TOKEN": config["token"],
        "WHATSAPP_PHONE_NUMBER_ID": config["phone_number_id"],
        "WEBHOOK_VERIFY_TOKEN": config["verify_token"],
    }
    missing = [name for name, value in required.items() if not value]
    return {
        "configured": not missing,
        "missing": missing,
        "signature_validation": bool(config["app_secret"]),
        "business_account_configured": bool(config["business_account_id"]),
        "webhook_url": "https://sistemataup.online/api/core/webhook/whatsapp",
    }


def is_whatsapp_send_ready() -> bool:
    config = get_whatsapp_config()
    return bool(config["token"] and config["phone_number_id"])


async def send_text_message(to: str, text: str) -> bool:
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
