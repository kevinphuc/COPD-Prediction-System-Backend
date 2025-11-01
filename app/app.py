from app.core.config import settings
from supabase import create_client, Client
from sqlmodel import create_engine, Session
# from typing import Generator
from collections.abc import Generator

# ==================================
# === SUPABASE-PY CLIENTS (Auth/Storage)
# ==================================

# Client dùng ANON key (cho login/register)
supabase_anon_client: Client = create_client(
    settings.SUPABASE_URL, 
    settings.SUPABASE_ANON_KEY
)

# Client dùng SERVICE ROLE key (cho các tác vụ backend, vd: upload storage)
supabase_service_client: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)


# ==================================
# === SQLMODEL ENGINE (Database)
# ==================================

# Engine kết nối CSDL PostgreSQL
engine = create_engine(
    settings.DATABASE_URL, 
    echo=True # Bật log SQL, tắt khi deploy
)

def get_db_session() -> Generator[Session, None, None]:
    """
    Tạo ra một session CSDL cho mỗi request.
    Đây là dependency sẽ được dùng trong app/dependencies/database.py
    (Mặc dù tôi đặt nó ở đây để tiện import)
    """
    with Session(engine) as session:
        yield session