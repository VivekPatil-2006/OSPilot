import os
import pytest
from app.services.file_scanner import FileScannerService

def test_file_scanner_text_chunking():
    scanner = FileScannerService()
    sample_text = "word " * 600
    chunks = scanner.chunk_text(sample_text, chunk_size=500, overlap=50)
    assert len(chunks) == 2

def test_scan_directory_recursive(tmp_path):
    # Setup test directory structure
    subfolder = tmp_path / "documents"
    subfolder.mkdir()
    
    file1 = tmp_path / "test1.txt"
    file1.write_text("Java Spring Boot Developer Resume", encoding="utf-8")
    
    file2 = subfolder / "test2.md"
    file2.write_text("Python FastAPI Machine Learning Engineer", encoding="utf-8")

    scanner = FileScannerService()
    docs = scanner.scan_directory(str(tmp_path), recursive=True)

    assert len(docs) == 2
    filenames = [doc["filename"] for doc in docs]
    assert "test1.txt" in filenames
    assert "test2.md" in filenames
