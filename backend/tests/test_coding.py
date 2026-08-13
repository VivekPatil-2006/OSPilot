import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.coding_assistant_service import coding_assistant_service

client = TestClient(app)

def test_read_project():
    res = coding_assistant_service.read_project(os.getcwd(), max_files=20)
    assert "project_path" in res
    assert res["total_files"] > 0
    assert len(res["file_tree"]) > 0

def test_explain_code():
    code = "def calculate_total(prices):\n    return sum(prices)"
    res = coding_assistant_service.explain_code(code, language="python")
    assert res["language"] == "python"
    assert len(res["explanation"]) > 0

def test_generate_code():
    prompt = "Write a Python function to compute factorial of n"
    res = coding_assistant_service.generate_code(prompt, language="python")
    assert res["language"] == "python"
    assert "def " in res["generated_code"] or "factorial" in res["generated_code"].lower()

def test_debug_code():
    buggy_code = "def add(a, b):\n    return a + c"
    err_log = "NameError: name 'c' is not defined"
    res = coding_assistant_service.debug_code(buggy_code, error_log=err_log, language="python")
    assert res["language"] == "python"
    assert len(res["diagnosis"]) > 0

def test_suggest_improvements():
    code = "def find_even(nums):\n    evens = []\n    for n in nums:\n        if n % 2 == 0:\n            evens.append(n)\n    return evens"
    res = coding_assistant_service.suggest_improvements(code, aspect="performance", language="python")
    assert res["aspect"] == "performance"
    assert len(res["suggestions"]) > 0

def test_generate_documentation():
    code = "def multiply(x, y):\n    return x * y"
    res = coding_assistant_service.generate_documentation(code, doc_format="docstring")
    assert res["doc_format"] == "docstring"
    assert len(res["documentation"]) > 0

def test_answer_repo_question():
    res = coding_assistant_service.answer_repo_question("Where is database session initialized?", project_path=os.getcwd())
    assert "question" in res
    assert len(res["answer"]) > 0

# --- API Endpoints Tests ---

def test_api_coding_read_project():
    response = client.post("/api/v1/coding/read-project", json={"project_path": os.getcwd(), "max_files": 10})
    assert response.status_code == 200
    data = response.json()
    assert data["total_files"] > 0

def test_api_coding_explain():
    response = client.post("/api/v1/coding/explain", json={"code_snippet": "x = 10", "language": "python"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["explanation"]) > 0

def test_api_coding_generate():
    response = client.post("/api/v1/coding/generate", json={"prompt": "Create hello world function", "language": "python"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["generated_code"]) > 0

def test_api_coding_debug():
    response = client.post("/api/v1/coding/debug", json={"code_snippet": "print(x)", "error_log": "NameError: name 'x' is not defined"})
    assert response.status_code == 200
    data = response.json()
    assert len(data["diagnosis"]) > 0
