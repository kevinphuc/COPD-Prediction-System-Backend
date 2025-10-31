from fastapi import FastAPI
from app.api.v1.api import api_router_v1

# Khởi tạo FastAPI app
app = FastAPI(
    title="Health Prediction API - Đồ án tốt nghiệp (SQLModel)",
    description="API sử dụng FastAPI, SQLModel và Supabase (Auth/Storage).",
    version="2.0.0"
)

# Gắn router v1
app.include_router(api_router_v1, prefix="/api/v1")

@app.get("/")
async def root():
    """Endpoint gốc chào mừng"""
    return {
        "message": "Chào mừng bạn đến với Health Prediction API v2 (SQLModel).",
        "docs_url": "/docs",
    }

