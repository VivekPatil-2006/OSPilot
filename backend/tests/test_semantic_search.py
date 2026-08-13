import os
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.db.models import FileDocument
from app.services.faiss_service import faiss_service
from app.services.semantic_search_service import semantic_search_service

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_and_faiss():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    faiss_service.clear()
    yield
    faiss_service.clear()

def test_semantic_file_search_flow(tmp_path):
    # Create sample test files
    resume_file = tmp_path / "java_resume.txt"
    resume_file.write_text(
        "Senior Java Developer Resume with Spring Boot, Microservices, Hibernate, and SQL databases expertise.",
        encoding="utf-8"
    )

    recipe_file = tmp_path / "pasta_recipe.txt"
    recipe_file.write_text(
        "Italian Pasta Recipe with fresh tomato sauce, garlic, olive oil, and basil leaves.",
        encoding="utf-8"
    )

    db = SessionLocal()
    try:
        # Index folder
        index_res = semantic_search_service.index_folder(db, str(tmp_path), recursive=True)
        assert index_res["files_found"] == 2
        assert index_res["chunks_indexed"] == 2

        # Natural Language Search Query
        search_res = semantic_search_service.search(db, "Find my Java resume", top_k=2)
        assert search_res["total_found"] > 0
        
        top_hit = search_res["results"][0]

        # Verify exact required fields: filename, score, location
        assert top_hit["filename"] == "java_resume.txt"
        assert top_hit["location"] == os.path.abspath(str(resume_file))
        assert "score" in top_hit
        assert top_hit["score"] > 0.0

    finally:
        db.close()

def test_search_api_endpoints(tmp_path):
    doc_file = tmp_path / "python_guide.md"
    doc_file.write_text("Complete Guide to Python Asyncio and FastAPI Backend Engineering.", encoding="utf-8")

    # Index API request
    idx_resp = client.post("/api/v1/search/index", json={"folder_path": str(tmp_path), "recursive": True})
    assert idx_resp.status_code == 200
    assert idx_resp.json()["files_found"] == 1

    # Search API query request
    query_resp = client.post("/api/v1/search/query", json={"query": "Python FastAPI guide", "top_k": 5})
    assert query_resp.status_code == 200
    data = query_resp.json()
    assert data["total_found"] >= 1
    assert data["results"][0]["filename"] == "python_guide.md"
    assert data["results"][0]["location"] == os.path.abspath(str(doc_file))
    assert isinstance(data["results"][0]["score"], float)
