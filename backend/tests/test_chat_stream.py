import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_system_metrics_endpoint():
    response = client.get("/api/v1/health/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cpu_percent" in data
    assert "ram_percent" in data
    assert "disk_percent" in data
    assert data["status"] == "ok"

def test_chat_stream_endpoint():
    response = client.post("/api/v1/chat/stream", json={
        "prompt": "Say hello in 3 words",
        "model": "qwen2.5-coder:7b"
    })
    assert response.status_code == 200
    assert "text/event-stream" in response.headers.get("content-type", "")
    
    # Read streamed text chunks
    content = response.text
    assert "data: " in content
    assert '"done"' in content
