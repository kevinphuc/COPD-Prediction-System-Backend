from app.db.supabase import supabase_anon_client
from app.models.base import UserCreateSchema, UserLoginSchema
from fastapi import HTTPException


class AuthService:
    def __init__(self):
        self.client = supabase_anon_client

    async def register(self, user_data: UserCreateSchema):
        """
        Code đăng ký user.
        Trigger trong Supabase sẽ tự động copy user sang public.users
        """
        try:
            user_metadata = {
                "username": user_data.username,
                "phone_number": user_data.phone_number,
            }

            session = self.client.auth.sign_up(
                {
                    "email": user_data.email,
                    "password": user_data.password,
                    "options": {"data": user_metadata},
                }
            )

            if not session or not session.user:
                raise HTTPException(status_code=400, detail="Không thể đăng ký user")

            return {
                "message": "Đăng ký thành công. Vui lòng kiểm tra email để xác thực."
            }

        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Lỗi đăng ký: {e}")

    async def login(self, login_data: UserLoginSchema):
        """Code đăng nhập user"""
        try:
            session = self.client.auth.sign_in_with_password(
                {
                    "email": login_data.email,
                    "password": login_data.password,
                }
            )
            if not session.session or not session.user:
                raise HTTPException(
                    status_code=401, detail="Email hoặc mật khẩu không đúng"
                )

            return {
                "access_token": session.session.access_token,
                "token_type": "bearer",
                "user_id": session.user.id,
            }
        except Exception:
            raise HTTPException(
                status_code=401, detail="Email hoặc mật khẩu không đúng"
            )


auth_service = AuthService()
