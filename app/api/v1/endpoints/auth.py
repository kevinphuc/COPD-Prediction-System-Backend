from fastapi import APIRouter, status, Depends
from app.models.base import UserCreateSchema, UserLoginSchema, TokenResponseSchema
from app.services.auth_service import auth_service

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreateSchema):
    """Đăng ký user mới (qua Supabase Auth)"""
    return await auth_service.register(user_data)

@router.post("/login", response_model=TokenResponseSchema)
async def login_user(form_data: UserLoginSchema):
    """Đăng nhập (qua Supabase Auth)"""
    return await auth_service.login(form_data)
