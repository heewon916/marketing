from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_inference_placeholder() -> None:
    response = client.post("/ai/inference", json={"prompt": "hello"})

    assert response.status_code == 200
    body = response.json()
    assert body["provider"] == "openai"
    assert body["model"] == "gpt-4o-mini"
    assert body["prompt"] == "hello"
