import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.memory_system_service import memory_system_service

client = TestClient(app)

def test_short_term_memory():
    session_id = "test-mem-session"
    memory_system_service.add_short_term_turn(session_id, "user", "What is Python?")
    memory_system_service.add_short_term_turn(session_id, "assistant", "Python is a programming language.")
    
    turns = memory_system_service.get_short_term_memory(session_id, limit=5)
    assert len(turns) >= 2
    assert turns[-1]["role"] == "assistant"

def test_remember_fact_and_vector_indexing():
    fact = "Remember this: my preferred theme is dark glassmorphism"
    res = memory_system_service.remember_fact(fact, category="user_pref")
    assert res["status"] == "stored"
    assert "theme" in res["fact"] or "glassmorphism" in res["fact"]

def test_query_memory_natural_language():
    res = memory_system_service.query_memory("What did I ask yesterday?", session_id="test-mem-session")
    assert "query" in res
    assert len(res["answer"]) > 0

def test_preferences_storage():
    memory_system_service.set_preference("default_browser", "msedge")
    prefs = memory_system_service.get_preferences()
    assert prefs.get("default_browser") == "msedge"

def test_task_history_logging():
    memory_system_service.log_task("open_website", "success", "Opened https://google.com")
    history = memory_system_service.get_task_history(limit=10)
    assert len(history) > 0
    assert history[0]["action"] == "open_website"

# --- REST API Endpoints Tests ---

def test_api_memory_remember():
    response = client.post("/api/v1/memory/remember", json={
        "fact": "Remember this: my API key is local_secret_123",
        "category": "credentials"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stored"

def test_api_memory_query():
    response = client.post("/api/v1/memory/query", json={
        "query": "What is my API key?",
        "session_id": "test-session"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["answer"]) > 0

def test_api_memory_preferences():
    # Set preference
    set_res = client.post("/api/v1/memory/preferences", json={"key": "font_size", "value": "14px"})
    assert set_res.status_code == 200
    
    # Get preferences
    get_res = client.get("/api/v1/memory/preferences")
    assert get_res.status_code == 200
    assert get_res.json()["preferences"].get("font_size") == "14px"

def test_api_memory_tasks():
    response = client.get("/api/v1/memory/tasks")
    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data
