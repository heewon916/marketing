import json
from uuid import uuid4

import fakeredis
from fastapi.testclient import TestClient

from app.services.sessions import session_key

VALID_PAYLOAD = {
    "store_id": str(uuid4()),
    "utterance": "오늘 가게에 찻잔, 곰돌이 인형, 원목 찬장을 자랑하고 싶어",
    "owner_persona": "aesthetic",
    "date": "2026-04-27",
    "weather": {"condition": "비", "temperature": 18.5},
}


def test_process_utterance_returns_session_id_and_guide(client: TestClient) -> None:
    session_id = "redis-session-id-123"

    response = client.post(
        f"/api/v1/ai/sessions/{session_id}/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session_id
    assert isinstance(body["guide_text"], str)
    assert len(body["guide_text"]) > 0


def test_keywords_hidden_when_debug_off(client: TestClient) -> None:
    response = client.post(
        "/api/v1/ai/sessions/sess-1/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200
    assert "keywords" not in response.json()


def test_keywords_exposed_when_debug_on(
    client: TestClient, debug_mode: None
) -> None:
    response = client.post(
        "/api/v1/ai/sessions/sess-2/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200
    body = response.json()
    assert "keywords" in body
    assert isinstance(body["keywords"], list)
    assert len(body["keywords"]) > 0


def test_empty_utterance_rejected(client: TestClient) -> None:
    payload = dict(VALID_PAYLOAD)
    payload["utterance"] = ""

    response = client.post(
        "/api/v1/ai/sessions/sess-3/process-utterance",
        json=payload,
    )

    assert response.status_code == 422


def test_missing_owner_persona_rejected(client: TestClient) -> None:
    payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "owner_persona"}

    response = client.post(
        "/api/v1/ai/sessions/sess-4/process-utterance",
        json=payload,
    )

    assert response.status_code == 422


def test_invalid_temperature_rejected(client: TestClient) -> None:
    payload = dict(VALID_PAYLOAD)
    payload["weather"] = {"condition": "비", "temperature": "hot"}

    response = client.post(
        "/api/v1/ai/sessions/sess-5/process-utterance",
        json=payload,
    )

    assert response.status_code == 422


def test_redis_payload_persisted(
    client: TestClient, fake_redis_sync: fakeredis.FakeStrictRedis
) -> None:
    session_id = "sess-redis-1"

    response = client.post(
        f"/api/v1/ai/sessions/{session_id}/process-utterance",
        json=VALID_PAYLOAD,
    )

    assert response.status_code == 200

    raw = fake_redis_sync.get(session_key(session_id))
    assert raw is not None
    saved = json.loads(raw)

    assert saved["session_id"] == session_id
    assert saved["store_id"] == VALID_PAYLOAD["store_id"]
    assert saved["status"] == "GUIDE_CREATED"
    assert isinstance(saved["keywords"], list) and len(saved["keywords"]) > 0
    assert isinstance(saved["draft_caption"], str)
    assert isinstance(saved["draft_hashtags"], list)
    assert saved["owner_persona"] == "aesthetic"
    assert saved["weather"] == {"condition": "비", "temperature": 18.5}
    assert saved["date"] == "2026-04-27"
    assert "expires_at" in saved


def test_redis_ttl_set(
    client: TestClient, fake_redis_sync: fakeredis.FakeStrictRedis
) -> None:
    session_id = "sess-ttl-1"

    response = client.post(
        f"/api/v1/ai/sessions/{session_id}/process-utterance",
        json=VALID_PAYLOAD,
    )
    assert response.status_code == 200

    ttl = fake_redis_sync.ttl(session_key(session_id))
    assert ttl > 0
