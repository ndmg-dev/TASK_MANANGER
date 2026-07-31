import logging
import smtplib
from email.message import EmailMessage
from email.utils import formataddr

from app.config import Config

logger = logging.getLogger(__name__)


class EmailService:
    """Envio de e-mail transacional via SMTP (Google Workspace)."""

    @staticmethod
    def is_configured():
        return bool(Config.SMTP_HOST and Config.SMTP_USER and Config.SMTP_PASSWORD)

    @staticmethod
    def send(to_email, subject, html_body, text_body=None):
        """Envia um e-mail. Retorna True em caso de sucesso."""
        if not EmailService.is_configured():
            logger.warning("[Email] SMTP não configurado — envio ignorado (%s)", subject)
            return False

        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = formataddr((Config.SMTP_FROM_NAME, Config.SMTP_FROM_EMAIL))
        message["To"] = to_email
        message.set_content(text_body or "Abra em um cliente com suporte a HTML.")
        message.add_alternative(html_body, subtype="html")

        try:
            if Config.SMTP_PORT == 465:
                with smtplib.SMTP_SSL(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20) as smtp:
                    smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                    smtp.send_message(message)
            else:
                with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=20) as smtp:
                    smtp.ehlo()
                    if Config.SMTP_USE_TLS:
                        smtp.starttls()
                        smtp.ehlo()
                    smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
                    smtp.send_message(message)

            logger.info("[Email] Enviado para %s — %s", to_email, subject)
            return True

        except Exception as e:
            logger.error("[Email] Falha ao enviar para %s: %s", to_email, e, exc_info=True)
            return False
