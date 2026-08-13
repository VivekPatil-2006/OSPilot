from fastapi import APIRouter, HTTPException
from app.domain.schemas import (
    MultiAgentExecuteRequest,
    MultiAgentExecuteResponse,
    AgentStateResponse
)
from app.services.multi_agent_service import multi_agent_service

router = APIRouter(prefix="/agents", tags=["LangGraph Multi-Agent Architecture"])


@router.post("/execute", response_model=MultiAgentExecuteResponse)
def execute_multi_agent_workflow(request: MultiAgentExecuteRequest) -> MultiAgentExecuteResponse:
    """Executes multi-agent workflow using LangGraph StateGraph (Planner, Retriever, Automation, Coding, Memory)."""
    try:
        res = multi_agent_service.execute_multi_agent_workflow(
            user_request=request.user_request,
            session_id=request.session_id,
            parallel_mode=request.parallel_mode,
            model=request.model
        )
        return MultiAgentExecuteResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/state/{session_id}", response_model=AgentStateResponse)
def get_agent_state(session_id: str) -> AgentStateResponse:
    """Retrieves conversation state history and execution metrics for a session ID."""
    try:
        res = multi_agent_service.get_session_state(session_id=session_id)
        return AgentStateResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
