import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

from services.whatsapp_client import get_whatsapp_config, whatsapp_connection_status
from services.whatsapp_link import get_whatsapp_mode

router = APIRouter(prefix="/admin", tags=["admin"])

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "admin.html"


def _mask_secret(value: str) -> str:
    if not value:
        return "(no configurado)"
    if len(value) <= 8:
        return "****"
    return f"{value[:4]}…{value[-4:]}"


def _read_env_config() -> dict[str, str]:
    config = get_whatsapp_config()
    mode = get_whatsapp_mode()
    env_config: dict[str, str] = {
        "WHATSAPP_MODE": mode,
        "CORE_HOST": os.getenv("CORE_HOST", "127.0.0.1"),
        "CORE_PORT": os.getenv("CORE_PORT", "3040"),
        "CORE_DB_PATH": os.getenv("CORE_DB_PATH", "./data/conversations.db"),
        "WHATSAPP_PHONE": os.getenv("WHATSAPP_PHONE", "(no configurado)"),
        "DEBUG": os.getenv("DEBUG", "false"),
    }
    if mode == "api":
        env_config.update(
            {
                "WHATSAPP_PHONE_NUMBER_ID": config["phone_number_id"] or "(no configurado)",
                "WHATSAPP_BUSINESS_ACCOUNT_ID": config["business_account_id"] or "(no configurado)",
                "WHATSAPP_TOKEN": _mask_secret(config["token"]),
                "WEBHOOK_VERIFY_TOKEN": _mask_secret(config["verify_token"]),
                "WHATSAPP_APP_SECRET": "configurado" if config["app_secret"] else "(no configurado)",
            }
        )
    return env_config


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def admin_page() -> HTMLResponse:
    return HTMLResponse(content=TEMPLATE_PATH.read_text(encoding="utf-8"))


@router.get("/status")
def admin_status() -> JSONResponse:
    from models.responses import HealthResponse

    health = HealthResponse()
    whatsapp = whatsapp_connection_status()
    return JSONResponse(
        content={
            "health": health.model_dump(),
            "config": _read_env_config(),
            "whatsapp": whatsapp,
        }
    )
