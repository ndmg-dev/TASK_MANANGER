from supabase import create_client, Client
from app.config import Config

supabase: Client = None


def init_supabase():
    """Initialize Supabase client with service role key for backend operations."""
    global supabase
    supabase = create_client(Config.SUPABASE_URL, Config.SUPABASE_SERVICE_ROLE_KEY)
    return supabase


def get_supabase() -> Client:
    """Get the initialized Supabase client."""
    global supabase
    if supabase is None:
        return init_supabase()
    return supabase
