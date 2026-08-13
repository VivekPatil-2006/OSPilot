from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.domain.schemas import (
    IndexFolderRequest, IndexFolderResponse,
    SearchQueryRequest, SearchQueryResponse
)
from app.services.semantic_search_service import semantic_search_service

router = APIRouter(prefix="/search", tags=["Semantic Search"])

@router.post("/index", response_model=IndexFolderResponse)
def index_folder(request: IndexFolderRequest, db: Session = Depends(get_db)) -> IndexFolderResponse:
    """Recursively scans directory, generates nomic embeddings, stores vectors in FAISS, and metadata in SQLite."""
    try:
        res = semantic_search_service.index_folder(
            db=db,
            folder_path=request.folder_path,
            recursive=request.recursive,
            clear_existing=request.clear_existing
        )
        return IndexFolderResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/query", response_model=SearchQueryResponse)
def search_query(request: SearchQueryRequest, db: Session = Depends(get_db)) -> SearchQueryResponse:
    """Executes natural language semantic search over indexed documents."""
    try:
        res = semantic_search_service.search(
            db=db,
            query=request.query,
            top_k=request.top_k,
            folder_path=request.folder_path
        )
        return SearchQueryResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
