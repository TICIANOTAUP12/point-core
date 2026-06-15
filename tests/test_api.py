import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(temp_db: str) -> TestClient:
    from main import app

    return TestClient(app)


class TestAPI:
    def test_health(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "core"

    def test_admin_page(self, client: TestClient) -> None:
        response = client.get("/admin")
        assert response.status_code == 200
        assert "Point Once Core" in response.text
        assert "Caso 1" in response.text
        assert "Caso 2" in response.text

    def test_admin_status(self, client: TestClient) -> None:
        response = client.get("/admin/status")
        assert response.status_code == 200
        data = response.json()
        assert data["health"]["status"] == "ok"
        assert "CORE_HOST" in data["config"]

    def test_chat_message(self, client: TestClient) -> None:
        response = client.post(
            "/chat/message",
            json={"phone": "5492612345678", "text": "hola quiero 2 cymax"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert data["state"] == "confirming"
        assert any(i["type"] == "combo_compra" for i in data["intents"])
        assert "$2.100.000" in data["reply"]

    def test_webhook_simple_payload(self, client: TestClient) -> None:
        response = client.post(
            "/webhook/whatsapp",
            json={"phone": "5492612345678", "text": "tienen stock?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert any(i["type"] == "consulta_stock" for i in data["intents"])

    def test_conversation_debug(self, client: TestClient) -> None:
        phone = "5492699999999"
        client.post("/chat/message", json={"phone": phone, "text": "hola"})
        response = client.get(f"/conversations/{phone}")
        assert response.status_code == 200
        assert response.json()["phone"] == phone

    def test_response_time_under_100ms(self, client: TestClient) -> None:
        import time

        start = time.perf_counter()
        response = client.post(
            "/chat/message",
            json={"phone": "5492611111111", "text": "precio caución y locales"},
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert response.status_code == 200
        assert elapsed_ms < 100, f"took {elapsed_ms:.1f}ms"
