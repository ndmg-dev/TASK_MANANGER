import atexit
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import Config

logger = logging.getLogger(__name__)

_scheduler = None


def _run_due_date_scan():
    """Job diário: avisa por e-mail quem tem atividade perto de vencer."""
    from app.services.notification_service import NotificationService

    try:
        result = NotificationService.run_due_date_scan()
        logger.info("[Scheduler] Varredura de prazos concluída: %s", result.get("enviados"))
    except Exception as e:
        logger.error("[Scheduler] Falha na varredura de prazos: %s", e, exc_info=True)


def start_scheduler():
    """
    Inicia o agendador em background.

    Rodando com múltiplos workers do gunicorn, cada um levanta seu próprio
    scheduler — a duplicidade de e-mail é barrada pela UNIQUE de
    ticket_notifications_log, não por lock de processo.
    """
    global _scheduler

    if not Config.SCHEDULER_ENABLED:
        logger.info("[Scheduler] Desabilitado por configuração")
        return None

    if _scheduler is not None:
        return _scheduler

    _scheduler = BackgroundScheduler(timezone=Config.TIMEZONE)
    _scheduler.add_job(
        _run_due_date_scan,
        trigger=CronTrigger(hour=Config.SCHEDULER_HOUR, minute=Config.SCHEDULER_MINUTE),
        id="due_date_scan",
        name="Avisos de prazo por e-mail",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
    )
    _scheduler.start()

    logger.info(
        "[Scheduler] Ativo — varredura diária às %02d:%02d (%s)",
        Config.SCHEDULER_HOUR, Config.SCHEDULER_MINUTE, Config.TIMEZONE,
    )

    atexit.register(lambda: _scheduler.shutdown(wait=False))
    return _scheduler
