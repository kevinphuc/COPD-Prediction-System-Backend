from app.db.supabase import get_db_session

# Dependency này chỉ đơn giản là gọi lại hàm get_db_session
# để chúng ta có thể import `Depends(get_session)`
get_session = get_db_session
