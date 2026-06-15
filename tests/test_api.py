import hashlib
import hmac
import json
import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(temp_db: str) -> TestClient:
    from main import app

    return TestClient(app)


META_WEBHOOK_PAYLOAD = {
    "object": "whatsapp_business_account",
    "entry": [
        {
            "id": "WABA_ID",
            "changes": [
                {
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "542646281854",
                            "phone_number_id": "PHONE_NUMBER_ID",
                        },
                        "messages": [
                            {
                                "from": "5492612345678",
                                "id": "wamid.test",
                                "timestamp": "1710000000",
                                "text": {"body": "tienen stock?"},
                                "type": "text",
                            }
                        ],
                    },
                    "field": "messages",
                }
            ],
        }
    ],
}


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
        assert "whatsapp" in data
        assert "configured" in data["whatsapp"]
        assert "webhook_url" in data["whatsapp"]

    def test_webhook_verify_success(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEBHOOK_VERIFY_TOKEN", "test-verify-token")
        response = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-verify-token",
                "hub.challenge": "challenge-12345",
            },
        )
        assert response.status_code == 200
        assert response.text == "challenge-12345"

    def test_webhook_verify_failure(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WEBHOOK_VERIFY_TOKEN", "correct-token")
        response = client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "challenge-12345",
            },
        )
        assert response.status_code == 403

    def test_webhook_meta_payload_mock_mode(self, client: TestClient) -> None:
        response = client.post("/webhook/whatsapp", json=META_WEBHOOK_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["sent"] is False

    def test_webhook_meta_payload_parse(self, client: TestClient) -> None:
        payload = {
            "entry": [
                {
                    "changes": [
                        {
                            "value": {
                                "messages": [
                                    {
                                        "from": "5492612345678",
                                        "text": {"body": "tienen stock?"},
                                    }
                                ]
                            }
                        }
                    ]
                }
            ]
        }
        response = client.post("/webhook/whatsapp", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert any(i["type"] == "consulta_stock" for i in data["intents"])

    def test_webhook_signature_validation(self, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("WHATSAPP_APP_SECRET", "test-app-secret")
        body = json.dumps({"phone": "5492612345678", "text": "hola"}).encode()
        digest = hmac.new(b"test-app-secret", body, hashlib.sha256).hexdigest()
        response = client.post(
            "/webhook/whatsapp",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": f"sha256={digest}",
            },
        )
        assert response.status_code == 200

        bad_response = client.post(
            "/webhook/whatsapp",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=invalid",
            },
        )
        assert bad_response.status_code == 403

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
