from fastapi import APIRouter, status, Depends
from fastapi.security import OAuth2PasswordRequestForm # <--- 1. Import cái này
from app.models.base import UserCreateSchema, UserLoginSchema, TokenResponseSchema
from app.services.auth_service import auth_service

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreateSchema):
    """Đăng ký user mới (qua Supabase Auth)"""
    return await auth_service.register(user_data)

@router.post("/login", response_model=TokenResponseSchema)
async def login_user(form_data: OAuth2PasswordRequestForm = Depends()): # <--- 2. Sử dụng Depends để lấy Form Data
    """
    Đăng nhập để lấy token.
    Sử dụng OAuth2PasswordRequestForm để tương thích với nút 'Authorize' trên Swagger UI.
    """
    
    # 3. Chuyển đổi dữ liệu từ Form của Swagger sang Schema mà Service cần
    # Lưu ý: OAuth2 form luôn gửi field tên là 'username', ta map nó vào 'email'
    user_login = UserLoginSchema(
        email=form_data.username, 
        password=form_data.password
    )
    
    # Gọi service như bình thường
    return await auth_service.login(user_login)