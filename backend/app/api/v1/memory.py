from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from app.domain.schemas import (
    RememberFactRequest, RememberFactResponse,
    QueryMemoryRequest, QueryMemoryResponse,
    SetPreferenceRequest, GetPreferencesResponse,
    GetTaskHistoryResponse, TaskHistoryItem
)
from app.services.memory_system_service import memory_system_service

router = APIRouter(prefix="/memory", tags=["Memory System"])


@router.post("/remember", response_model=RememberFactResponse)
def remember_fact(request: RememberFactRequest) -> RememberFactResponse:
    """Stores an explicit fact/instruction ('Remember this...') into Long-Term & FAISS Vector Memory."""
    try:
        res = memory_system_service.remember_fact(
            fact_text=request.fact,
            category=request.category or "general"
        )
        return RememberFactResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=QueryMemoryResponse)
def query_memory(request: QueryMemoryRequest) -> QueryMemoryResponse:
    """Handles natural language memory questions (e.g. 'What did I ask yesterday?' or 'What is my preferred browser?')."""
    try:
        res = memory_system_service.query_memory(
            query_text=request.query,
            session_id=request.session_id or "default-session"
        )
        return QueryMemoryResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}")
def get_conversation_history(session_id: str, timeframe: str = "yesterday"):
    """Retrieves conversation history for a session filtered by timeframe."""
    try:
        history = memory_system_service.query_conversation_history(
            session_id=session_id,
            timeframe=timeframe
        )
        return {"session_id": session_id, "timeframe": timeframe, "history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/preferences", response_model=GetPreferencesResponse)
def set_preference(request: SetPreferenceRequest) -> GetPreferencesResponse:
    """Sets a key-value user preference setting in SQLite."""
    try:
        memory_system_service.set_preference(key=request.key, value=request.value)
        prefs = memory_system_service.get_preferences()
        return GetPreferencesResponse(preferences=prefs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/preferences", response_model=GetPreferencesResponse)
def get_preferences() -> GetPreferencesResponse:
    """Retrieves all stored key-value user preferences from SQLite."""
    try:
        prefs = memory_system_service.get_preferences()
        return GetPreferencesResponse(preferences=prefs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks", response_model=GetTaskHistoryResponse)
def get_task_history(limit: int = 50) -> GetTaskHistoryResponse:
    """Retrieves recorded automated task execution logs from SQLite."""
    try:
        raw_tasks = memory_system_service.get_task_history(limit=limit)
        items = [TaskHistoryItem(**t) for t in raw_tasks]
        return GetTaskHistoryResponse(tasks=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
