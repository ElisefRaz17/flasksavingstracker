import os
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
options = ClientOptions(auto_refresh_token=False)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY,options)
