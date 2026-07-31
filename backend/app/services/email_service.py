import logging

import requests

from app.config import Config

logger = logging.getLogger(__name__)


class EmailService:
    """
    Envio de e-mail transacional pela API do Brevo.

    Só precisa da chave de API — sem login SMTP, sem senha de app. O remetente
    (BREVO_SENDER_EMAIL) precisa ser um sender validado no painel do Brevo.
    """

    TIMEOUT = 20

    @staticmethod
    def is_configured():
        return bool(Config.BREVO_API_KEY and Config.BREVO_SENDER_EMAIL)

    @staticmethod
    def send(to_email, subject, html_body, text_body=None, to_name=None):
        """Envia um e-mail. Retorna True em caso de sucesso."""
        if not EmailService.is_configured():
            logger.warning("[Email] Brevo não configurado — envio ignorado (%s)", subject)
            return False

        payload = {
            "sender": {
                "email": Config.BREVO_SENDER_EMAIL,
                "name": Config.BREVO_SENDER_NAME,
            },
            "to": [{"email": to_email, **({"name": to_name} if to_name else {})}],
            "subject": subject,
            "htmlContent": html_body,
        }
        if text_body:
            payload["textContent"] = text_body

        try:
            response = requests.post(
                Config.BREVO_API_URL,
                json=payload,
                headers={
                    "api-key": Config.BREVO_API_KEY,
                    "accept": "application/json",
                    "content-type": "application/json",
                },
                timeout=EmailService.TIMEOUT,
            )

            if response.status_code in (200, 201, 202):
                message_id = (response.json() or {}).get("messageId")
                logger.info("[Email] Enviado para %s — %s (id=%s)", to_email, subject, message_id)
                return True

            # 401 = chave inválida | 400 = remetente não validado, entre outros
            logger.error(
                "[Email] Brevo recusou o envio para %s: HTTP %s — %s",
                to_email, response.status_code, response.text[:300],
            )
            return False

        except Exception as e:
            logger.error("[Email] Falha ao enviar para %s: %s", to_email, e, exc_info=True)
            return False
