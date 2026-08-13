import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.multi_agent_service import multi_agent_service

client = TestClient(app)

def test_planner_and_execution_workflow():
    session_id = "test-session-1"
    req = "Explain this python function and search documents"
    res = multi_agent_service.execute_multi_agent_workflow(
        user_request=req,
        session_id=session_id,
        parallel_mode=True
    )
    assert res["session_id"] == session_id
    assert "plan" in res
    assert len(res["logs"]) > 0
    assert len(res["final_response"]) > 0

def test_memory_state_retention():
    session_id = "test-session-mem"
    req1 = "Hello, my name is Alex"
    res1 = multi_agent_service.execute_multi_agent_workflow(user_request=req1, session_id=session_id)
    
    state_res = multi_agent_service.get_session_state(session_id)
    assert state_res["session_id"] == session_id
    assert state_res["execution_count"] >= 1
    assert len(state_res["conversation_history"]) >= 1

def test_error_recovery_mechanism():
    # Force query that triggers warning/fallback path
    res = multi_agent_service.execute_multi_agent_workflow(
        user_request="click button and debug code",
        session_id="test-err-recovery"
    )
    assert "final_response" in res
    assert len(res["logs"]) > 0

# --- REST API Endpoints Tests ---

def test_api_agents_execute():
    response = client.post("/api/v1/agents/execute", json={
        "user_request": "Write a python script to search files",
        "session_id": "api-test-session",
        "parallel_mode": True
    })
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "api-test-session"
    assert "plan" in data
    assert "final_response" in data

def test_api_agents_state():
    response = client.get("/api/v1/agents/state/api-test-session")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == "api-test-session"
    assert "execution_count" in data
