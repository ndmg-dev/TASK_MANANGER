import os
from dotenv import load_dotenv

load_dotenv()


# Orquestradores como o Coolify repassam TODA variável declarada no compose,
# mesmo as não preenchidas — elas chegam como string vazia, e não ausentes.
# Por isso "" é tratado aqui como "não informado", senão o default nunca vale.

def env_str(key, default=None):
    value = os.environ.get(key)
    return value.strip() if value and value.strip() else default


def env_int(key, default):
    value = env_str(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def env_bool(key, default=False):
    value = env_str(key)
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on")


def env_list(key, default):
    value = env_str(key)
    if value is None:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


class Config:
    SECRET_KEY = env_str("FLASK_SECRET_KEY", "dev-secret-key")
    SUPABASE_URL = env_str("SUPABASE_URL")
    SUPABASE_ANON_KEY = env_str("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_ROLE_KEY = env_str("SUPABASE_SERVICE_ROLE_KEY")
    GROQ_API_KEY = env_str("GROQ_API_KEY")
    FLASK_ENV = env_str("FLASK_ENV", "development")

    # GitHub Integration
    GITHUB_TOKEN = env_str("GITHUB_TOKEN")
    GITHUB_REPO_OWNER = env_str("GITHUB_REPO_OWNER")
    GITHUB_REPO_NAME = env_str("GITHUB_REPO_NAME")
    GITHUB_BASE_BRANCH = env_str("GITHUB_BASE_BRANCH", "main")

    # ─── Organização ────────────────────────────────────
    # Domínio corporativo aceito no login e nas rotas da API
    ALLOWED_EMAIL_DOMAIN = env_str("ALLOWED_EMAIL_DOMAIN", "mendoncagalvao.com.br")
    APP_BASE_URL = env_str("APP_BASE_URL", "http://localhost:3000")
    CORS_ORIGINS = env_list(
        "CORS_ORIGINS", ["http://localhost:3000", "http://localhost:5173"]
    )

    # ─── SMTP (avisos de prazo) ─────────────────────────
    SMTP_HOST = env_str("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = env_int("SMTP_PORT", 587)
    SMTP_USER = env_str("SMTP_USER")
    SMTP_PASSWORD = env_str("SMTP_PASSWORD")
    SMTP_USE_TLS = env_bool("SMTP_USE_TLS", True)
    SMTP_FROM_EMAIL = env_str("SMTP_FROM_EMAIL") or SMTP_USER
    SMTP_FROM_NAME = env_str("SMTP_FROM_NAME", "NDMG Task Manager")

    # ─── Automação de notificações ──────────────────────
    NOTIFICATIONS_ENABLED = env_bool("NOTIFICATIONS_ENABLED", True)
    SCHEDULER_ENABLED = env_bool("SCHEDULER_ENABLED", True)
    SCHEDULER_HOUR = env_int("SCHEDULER_HOUR", 8)
    SCHEDULER_MINUTE = env_int("SCHEDULER_MINUTE", 0)
    TIMEZONE = env_str("TIMEZONE", "America/Sao_Paulo")
    # Dias de antecedência que disparam aviso (0 = no dia do vencimento)
    NOTIFY_DAYS_BEFORE = [
        int(d) for d in env_list("NOTIFY_DAYS_BEFORE", ["3", "1", "0"]) if d.isdigit()
    ]
    # Avisa também quando o prazo já passou (status != Done)
    NOTIFY_OVERDUE = env_bool("NOTIFY_OVERDUE", True)
    # Token para disparar a automação manualmente via endpoint protegido
    AUTOMATION_TOKEN = env_str("AUTOMATION_TOKEN")
