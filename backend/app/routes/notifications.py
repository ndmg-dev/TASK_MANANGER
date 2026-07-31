import hmac
import logging

from flask import Blueprint, request, jsonify

from app.config import Config
from app.middleware.auth import require_admin
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.route("/notifications/status", methods=["GET"])
@require_admin
def notifications_status():
    """Diagnóstico da automação (admin)."""
    return jsonify({
        "notificacoes_ativas": Config.NOTIFICATIONS_ENABLED,
        "scheduler_ativo": Config.SCHEDULER_ENABLED,
        "horario": f"{Config.SCHEDULER_HOUR:02d}:{Config.SCHEDULER_MINUTE:02d}",
        "timezone": Config.TIMEZONE,
        "dias_de_antecedencia": Config.NOTIFY_DAYS_BEFORE,
        "avisa_atrasados": Config.NOTIFY_OVERDUE,
        "smtp_configurado": EmailService.is_configured(),
        "remetente": Config.SMTP_FROM_EMAIL,
    })


@notifications_bp.route("/notifications/run", methods=["POST"])
@require_admin
def run_now():
    """
    Dispara a varredura de prazos manualmente (admin).

    Use {"dry_run": true} para ver o que seria enviado sem enviar nada.
    """
    data = request.get_json(silent=True) or {}
    result = NotificationService.run_due_date_scan(dry_run=bool(data.get("dry_run")))
    return jsonify(result)


@notifications_bp.route("/notifications/cron", methods=["POST"])
def run_from_cron():
    """
    Gatilho externo (cron/monitor) protegido por AUTOMATION_TOKEN.

    Alternativa ao scheduler interno: mantenha SCHEDULER_ENABLED=false e
    chame este endpoint uma vez por dia.
    """
    if not Config.AUTOMATION_TOKEN:
        return jsonify({"error": "AUTOMATION_TOKEN não configurado"}), 503

    token = request.headers.get("X-Automation-Token", "")
    if not hmac.compare_digest(token, Config.AUTOMATION_TOKEN):
        return jsonify({"error": "Token inválido"}), 401

    return jsonify(NotificationService.run_due_date_scan())
