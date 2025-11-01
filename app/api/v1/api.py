from fastapi import APIRouter
from app.api.v1.endpoints import auth, health

api_router_v1 = APIRouter()

# Gắn các router của từng endpoint
api_router_v1.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router_v1.include_router(health.router, prefix="/health", tags=["Health Data"])
