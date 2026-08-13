import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.db.models import FileDocument
from app.services.document_loader import document_loader
from app.services.rag_service import rag_service

TEST_DB_URL = "sqlite:///:memory:"

@pytest.fixture
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_markdown_file(tmp_path):
    md_content = """# System Architecture Manual

## Section 1: Overview
OSPilot is an offline production-quality AI Desktop Assistant. It provides secure, local intelligent features without relying on external cloud endpoints.

## Section 2: Core Components
The system consists of an Electron frontend, a FastAPI backend, an SQLite metadata store, and FAISS vector database.

## Section 3: Data Security
All vector embeddings and document chunks are persisted strictly on local storage using AES encrypted SQLite.

## Section 4: Maintenance and Operations
Section 4 details maintenance procedures. To maintain optimal performance, clean vector indices quarterly and verify database schema integrity. Backups should be taken daily.
"""
    file_path = tmp_path / "sample_manual.md"
    file_path.write_text(md_content, encoding="utf-8")
    return str(file_path)


def test_document_loader_markdown(sample_markdown_file):
    chunks = document_loader.load_and_chunk_document(sample_markdown_file)
    assert len(chunks) >= 4
    section_titles = [c["section_title"] for c in chunks]
    assert "Section 1: Overview" in section_titles
    assert "Section 4: Maintenance and Operations" in section_titles


def test_rag_service_indexing_and_query(db_session, sample_markdown_file):
    # Index document
    index_res = rag_service.index_document(db_session, sample_markdown_file)
    assert index_res["chunks_indexed"] >= 4
    assert index_res["filename"] == "sample_manual.md"

    # Verify database records
    records = db_session.query(FileDocument).all()
    assert len(records) >= 4

    # Test Summarization
    summary_res = rag_service.summarize_document(db_session, filepath=sample_markdown_file)
    assert summary_res["filename"] == "sample_manual.md"
    assert len(summary_res["summary"]) > 0

    # Test General Q&A ("Ask questions")
    query_res = rag_service.query_document(
        db_session,
        query="What components make up the system?",
        filepath=sample_markdown_file
    )
    assert len(query_res["answer"]) > 0
    assert len(query_res["sources"]) > 0

    # Test Section targeting ("Explain section 4")
    sec_res = rag_service.query_document(
        db_session,
        query="Explain section 4",
        filepath=sample_markdown_file
    )
    assert len(sec_res["answer"]) > 0
    # Verify section 4 was matched in sources
    source_sections = [s["section_title"] for s in sec_res["sources"]]
    assert any("Section 4" in sec for sec in source_sections if sec)
