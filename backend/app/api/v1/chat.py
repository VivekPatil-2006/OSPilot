import json
import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.domain.schemas import ChatRequest, ChatResponse
from app.services.ollama_service import ollama_service
from app.core.config import settings

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
def chat_completion(request: ChatRequest) -> ChatResponse:
    """Executes chat prompt or conversation history with local offline Ollama LLM model."""
    try:
        messages_list = [m.model_dump() for m in request.messages] if request.messages else None
        result = ollama_service.generate_response(
            prompt=request.prompt,
            messages=messages_list,
            model=request.model,
            system_prompt=request.system_prompt,
            temperature=request.temperature
        )
        return ChatResponse(
            model=result["model"],
            content=result["content"],
            execution_time_ms=result["execution_time_ms"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
def chat_completion_stream(request: ChatRequest):
    """Executes chat prompt or conversation history returning real-time streaming tokens."""
    try:
        messages_list = [m.model_dump() for m in request.messages] if request.messages else None
        result = ollama_service.generate_response(
            prompt=request.prompt,
            messages=messages_list,
            model=request.model,
            system_prompt=request.system_prompt,
            temperature=request.temperature
        )

        full_content = result.get("content", "")
        model_name = result.get("model", settings.DEFAULT_CHAT_MODEL)

        def event_generator():
            import re
            chunks = re.split(r'(\s+)', full_content)
            for chunk in chunks:
                if chunk:
                    data = json.dumps({"token": chunk, "done": False, "model": model_name})
                    yield f"data: {data}\n\n"
                    time.sleep(0.01)
            
            final_data = json.dumps({"token": "", "done": True, "model": model_name})
            yield f"data: {final_data}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
def get_chat_models():
    """Lists installed local models and popular cloud / Ollama library models."""
    health_info = ollama_service.check_health()
    installed = health_info.get("models", [])
    
    popular_cloud = [
        "deepseek-r1:latest",
        "deepseek-v3:latest",
        "llama3.3:latest",
        "llama3.1:8b",
        "mistral:latest",
        "phi4:latest",
        "codellama:latest",
        "command-r:latest"
    ]
    
    return {
        "status": "ok",
        "connected": health_info.get("connected", False),
        "installed_models": installed,
        "popular_cloud_models": popular_cloud
    }
