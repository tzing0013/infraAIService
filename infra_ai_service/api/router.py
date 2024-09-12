from fastapi.routing import APIRouter

from infra_ai_service.api.ai_enhance.spec_repair_process import \
    router as spec_repair_process
from infra_ai_service.api.ai_enhance.text_process import \
    router as text_process_router
from infra_ai_service.api.ai_enhance.embedding import \
    router as embedding_router
from infra_ai_service.api.ai_enhance.vector_search import \
    router as vector_search_router

api_router = APIRouter()
api_router.include_router(spec_repair_process, prefix="/spec-repair",
                          tags=["repair"])
api_router.include_router(text_process_router, prefix="/text", tags=["text"])
api_router.include_router(embedding_router, prefix="/embedding",
                          tags=["embedding"])
api_router.include_router(vector_search_router, prefix="/search",
                          tags=["search"])
