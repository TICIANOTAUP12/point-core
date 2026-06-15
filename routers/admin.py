import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse, JSONResponse

router = APIRouter(prefix="/admin", tags=["admin"])

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "templates" / "admin.html"


def _read_env_config() -> dict[str, str]:
    return {
        "CORE_HOST": os.getenv("CORE_HOST", "127.0.0.1"),
        "CORE_PORT": os.getenv("CORE_PORT", "3040"),
        "CORE_DB_PATH": os.getenv("CORE_DB_PATH", "./data/conversations.db"),
        "WHATSAPP_PHONE": os.getenv("WHATSAPP_PHONE", "(no configurado)"),
        "DEBUG": os.getenv("DEBUG", "false"),
    }


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def admin_page() -> HTMLResponse:
    return HTMLResponse(content=TEMPLATE_PATH.read_text(encoding="utf-8"))


@router.get("/status")
def admin_status() -> JSONResponse:
    from models.responses import HealthResponse

    health = HealthResponse()
    return JSONResponse(
        content={
            "health": health.model_dump(),
            "config": _read_env_config(),
        }
    )
