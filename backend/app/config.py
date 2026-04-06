import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")

    # GitHub Integration
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
    GITHUB_REPO_OWNER = os.environ.get("GITHUB_REPO_OWNER")
    GITHUB_REPO_NAME = os.environ.get("GITHUB_REPO_NAME")
    GITHUB_BASE_BRANCH = os.environ.get("GITHUB_BASE_BRANCH", "main")
