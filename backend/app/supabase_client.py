from supabase import Client, create_client

from .config import supabase_secret_key, supabase_url


def get_supabase_client() -> Client:
    if not supabase_url or not supabase_secret_key:
        raise RuntimeError("Configura SUPABASE_URL y SUPABASE_SECRET_KEY en backend/.env")

    return create_client(supabase_url, supabase_secret_key)

