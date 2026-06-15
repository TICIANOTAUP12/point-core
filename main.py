import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from core.database import init_db
from models.responses import HealthResponse
from routers import admin, chat, webhook
from services.conversation import get_record

HOST = os.getenv("CORE_HOST", "127.0.0.1")
PORT = int(os.getenv("CORE_PORT", "3040"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Point Once Core",
    description="Rules-based NLU chat service for Agencia TA / Point Once",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(admin.router)
app.include_router(chat.router)
app.include_router(webhook.router)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse()


@app.get("/conversations/{phone}")
def get_conversation_debug(phone: str) -> dict[str, object]:
    record = get_record(phone)
    return record.model_dump(mode="json")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=HOST, port=PORT, workers=1, reload=False)
