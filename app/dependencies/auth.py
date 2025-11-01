from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.db.supabase import supabase_anon_client
from uuid import UUID

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user_id(token: str = Depends(oauth2_scheme)) -> UUID:
    """
    Dependency: Xác thực token JWT của Supabase và trả về user_id (UUID).
    """
    try:
        user_response = await supabase_anon_client.auth.get_user(token)
        user = user_response.user
        if user and user.id:
            return UUID(user.id) # Chuyển str sang UUID
        else:
            raise HTTPException(status_code=401, detail="Invalid user token")
    except Exception as e:
        print(f"Auth error: {e}")
        raise HTTPException(status_code=401, detail="Invalid authentication token")
