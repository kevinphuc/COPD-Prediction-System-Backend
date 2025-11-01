from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Tải biến môi trường từ file .env"""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    # Supabase API keys (cho Auth, Storage)
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    
    # Supabase DB Connection String (cho SQLModel)
    # Lấy từ Settings > Database > Connection string (URI)
    DATABASE_URL: str

# Khởi tạo settings
settings = Settings()
