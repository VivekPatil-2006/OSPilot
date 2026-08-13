from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.domain.schemas import (
    RAGIndexRequest, RAGIndexResponse,
    RAGSummarizeRequest, RAGSummarizeResponse,
    RAGQueryRequest, RAGQueryResponse
)
from app.services.rag_service import rag_service

router = APIRouter(prefix="/rag", tags=["RAG Document Assistant"])


@router.post("/index", response_model=RAGIndexResponse)
def index_document(request: RAGIndexRequest, db: Session = Depends(get_db)) -> RAGIndexResponse:
    """Indexes a single document file (PDF, DOCX, TXT, MD), creating embeddings in FAISS and SQLite metadata."""
    try:
        res = rag_service.index_document(db=db, filepath=request.filepath)
        return RAGIndexResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/summarize", response_model=RAGSummarizeResponse)
def summarize_document(request: RAGSummarizeRequest, db: Session = Depends(get_db)) -> RAGSummarizeResponse:
    """Generates an executive summary and section overview for an indexed document using local Ollama LLM."""
    try:
        res = rag_service.summarize_document(
            db=db,
            filepath=request.filepath,
            filename=request.filename
        )
        return RAGSummarizeResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/query", response_model=RAGQueryResponse)
def query_document(request: RAGQueryRequest, db: Session = Depends(get_db)) -> RAGQueryResponse:
    """Executes RAG Q&A or section explanations ('Ask questions', 'Explain section 4') over indexed documents."""
    try:
        res = rag_service.query_document(
            db=db,
            query=request.query,
            filepath=request.filepath,
            filename=request.filename,
            top_k=request.top_k,
            model=request.model
        )
        return RAGQueryResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
