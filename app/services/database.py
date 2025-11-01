from supabase import Client, create_client
from app.core.config import settings

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(
            settings.SUPABASE_URL, 
            settings.SUPABASE_KEY
        )
    
    def get_client(self) -> Client:
        return self.client

# Global instance
supabase_client = SupabaseClient()

def get_supabase() -> Client:
    return supabase_client.get_client()