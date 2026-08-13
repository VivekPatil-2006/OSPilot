from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.chat import router as chat_router
from app.api.v1.search import router as search_router
from app.api.v1.rag import router as rag_router
from app.api.v1.automation import router as automation_router
from app.api.v1.browser import router as browser_router
from app.api.v1.coding import router as coding_router
from app.api.v1.agents import router as agents_router
from app.api.v1.memory import router as memory_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(chat_router)
api_v1_router.include_router(search_router)
api_v1_router.include_router(rag_router)
api_v1_router.include_router(automation_router)
api_v1_router.include_router(browser_router)
api_v1_router.include_router(coding_router)
api_v1_router.include_router(agents_router)
api_v1_router.include_router(memory_router)







