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

    # ─── Organização ────────────────────────────────────
    # Domínio corporativo aceito no login e nas rotas da API
    ALLOWED_EMAIL_DOMAIN = os.environ.get("ALLOWED_EMAIL_DOMAIN", "mendoncagalvao.com.br")
    APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:3000")
    CORS_ORIGINS = [
        o.strip() for o in os.environ.get(
            "CORS_ORIGINS", "http://localhost:3000,http://localhost:5173"
        ).split(",") if o.strip()
    ]

    # ─── SMTP (avisos de prazo) ─────────────────────────
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
    SMTP_USE_TLS = os.environ.get("SMTP_USE_TLS", "true").lower() == "true"
    SMTP_FROM_EMAIL = os.environ.get("SMTP_FROM_EMAIL") or os.environ.get("SMTP_USER")
    SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "NDMG Task Manager")

    # ─── Automação de notificações ──────────────────────
    NOTIFICATIONS_ENABLED = os.environ.get("NOTIFICATIONS_ENABLED", "true").lower() == "true"
    SCHEDULER_ENABLED = os.environ.get("SCHEDULER_ENABLED", "true").lower() == "true"
    SCHEDULER_HOUR = int(os.environ.get("SCHEDULER_HOUR", 8))
    SCHEDULER_MINUTE = int(os.environ.get("SCHEDULER_MINUTE", 0))
    TIMEZONE = os.environ.get("TIMEZONE", "America/Sao_Paulo")
    # Dias de antecedência que disparam aviso (0 = no dia do vencimento)
    NOTIFY_DAYS_BEFORE = [
        int(d.strip())
        for d in os.environ.get("NOTIFY_DAYS_BEFORE", "3,1,0").split(",")
        if d.strip().isdigit()
    ]
    # Avisa também quando o prazo já passou (status != Done)
    NOTIFY_OVERDUE = os.environ.get("NOTIFY_OVERDUE", "true").lower() == "true"
    # Token para disparar a automação manualmente via endpoint protegido
    AUTOMATION_TOKEN = os.environ.get("AUTOMATION_TOKEN")
