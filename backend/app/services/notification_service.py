import logging
from datetime import date, datetime, timedelta
from html import escape
from zoneinfo import ZoneInfo

from app.config import Config
from app.extensions import get_supabase
from app.services.email_service import EmailService
from app.services.ticket_service import TicketService

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Avisos de prazo por e-mail.

    Regra: para cada ticket em aberto com `data_fim` preenchida, avisa o
    responsável e os participantes nos dias de antecedência configurados
    (NOTIFY_DAYS_BEFORE) e novamente quando o prazo estoura.

    A dedupe vive no banco: a UNIQUE de `ticket_notifications_log` garante
    que o mesmo aviso não sai duas vezes, mesmo com o scheduler rodando em
    múltiplos workers do gunicorn.
    """

    @staticmethod
    def _today():
        return datetime.now(ZoneInfo(Config.TIMEZONE)).date()

    @staticmethod
    def _recipients(ticket):
        """Responsável + participantes, deduplicados por e-mail."""
        people = {}

        assignee = ticket.get("assignee")
        if assignee and assignee.get("email"):
            people[assignee["email"]] = {
                "id": assignee.get("id"),
                "email": assignee["email"],
                "nome": assignee.get("full_name") or assignee["email"],
                "papel": "Responsável",
            }

        for participant in ticket.get("ticket_participants") or []:
            user = participant.get("users") or {}
            if user.get("email") and user["email"] not in people:
                people[user["email"]] = {
                    "id": user.get("id"),
                    "email": user["email"],
                    "nome": user.get("full_name") or user["email"],
                    "papel": "Participante",
                }

        return list(people.values())

    @staticmethod
    def _classify(dias_restantes):
        """(tipo, assunto_prefixo) para o número de dias até o vencimento."""
        if dias_restantes < 0:
            return "overdue", "Atrasada"
        if dias_restantes == 0:
            return "due_today", "Vence hoje"
        return "due_soon", f"Vence em {dias_restantes} dia{'s' if dias_restantes > 1 else ''}"

    @staticmethod
    def _claim(ticket, recipient, tipo, data_fim, dias_restantes):
        """
        Reserva o envio no log. Retorna o id da linha, ou None se o aviso
        já tinha sido enviado (violação da UNIQUE).
        """
        sb = get_supabase()
        try:
            result = sb.table("ticket_notifications_log").insert({
                "ticket_id": ticket["id"],
                "user_id": recipient.get("id"),
                "email": recipient["email"],
                "tipo": tipo,
                "data_referencia": data_fim.isoformat(),
                "dias_restantes": dias_restantes,
            }).execute()
            return result.data[0]["id"] if result.data else None
        except Exception:
            # Duplicate key = aviso já enviado nesta janela
            return None

    @staticmethod
    def _release(log_id):
        """Desfaz a reserva para que o aviso seja retentado amanhã."""
        if not log_id:
            return
        try:
            get_supabase().table("ticket_notifications_log").delete().eq("id", log_id).execute()
        except Exception as e:
            logger.error("[Notificações] Falha ao liberar log %s: %s", log_id, e)

    @staticmethod
    def _build_email(ticket, recipient, dias_restantes, data_fim):
        tipo, prefixo = NotificationService._classify(dias_restantes)

        titulo = ticket.get("titulo") or "Sem título"
        codigo = f"NDMG-{ticket['id'][:8]}"
        setor = (ticket.get("department") or {}).get("nome") or "Sem setor"
        status = ticket.get("status") or "-"
        prazo_br = data_fim.strftime("%d/%m/%Y")
        link = f"{Config.APP_BASE_URL.rstrip('/')}/?ticket={ticket['id']}"

        if tipo == "overdue":
            chamada = f"está <strong>atrasada há {abs(dias_restantes)} dia(s)</strong>."
            cor = "#ef4444"
        elif tipo == "due_today":
            chamada = "<strong>vence hoje</strong>."
            cor = "#f59e0b"
        else:
            chamada = f"vence em <strong>{dias_restantes} dia(s)</strong>."
            cor = "#d4a853"

        subject = f"[{prefixo}] {codigo} — {titulo}"

        html = f"""\
<div style="font-family:Segoe UI,Helvetica,Arial,sans-serif;background:#0b0b10;padding:32px;color:#e8e4dc">
  <div style="max-width:560px;margin:0 auto;background:#14141c;border:1px solid #26262f;border-radius:12px;overflow:hidden">
    <div style="height:4px;background:{cor}"></div>
    <div style="padding:28px">
      <p style="margin:0 0 4px;font-size:12px;letter-spacing:2px;text-transform:uppercase;color:#8b8794">
        NDMG Task Manager
      </p>
      <h1 style="margin:0 0 16px;font-size:20px;color:#f5f0e8">Olá, {escape(recipient['nome'].split(' ')[0])}!</h1>
      <p style="margin:0 0 20px;font-size:14px;line-height:1.6;color:#c9c4bb">
        A atividade abaixo, na qual você é <strong>{recipient['papel'].lower()}</strong>, {chamada}
      </p>
      <div style="background:#0b0b10;border:1px solid #26262f;border-radius:8px;padding:18px;margin-bottom:22px">
        <p style="margin:0 0 6px;font-size:11px;color:{cor};font-weight:700;letter-spacing:1px">{codigo}</p>
        <p style="margin:0 0 12px;font-size:16px;font-weight:600;color:#f5f0e8">{escape(titulo)}</p>
        <table style="font-size:13px;color:#c9c4bb;border-collapse:collapse">
          <tr><td style="padding:3px 16px 3px 0;color:#8b8794">Setor</td><td>{escape(setor)}</td></tr>
          <tr><td style="padding:3px 16px 3px 0;color:#8b8794">Status</td><td>{escape(status)}</td></tr>
          <tr><td style="padding:3px 16px 3px 0;color:#8b8794">Prazo</td><td style="color:{cor};font-weight:600">{prazo_br}</td></tr>
        </table>
      </div>
      <a href="{link}" style="display:inline-block;background:#d4a853;color:#050508;text-decoration:none;
         padding:11px 22px;border-radius:8px;font-weight:700;font-size:14px">Abrir no Kanban</a>
      <p style="margin:24px 0 0;font-size:11px;color:#6e6a75;line-height:1.5">
        Você recebeu este aviso automático porque está vinculado a esta atividade.
      </p>
    </div>
  </div>
</div>"""

        text = (
            f"{prefixo}: {codigo} — {titulo}\n"
            f"Setor: {setor} | Status: {status} | Prazo: {prazo_br}\n"
            f"Abrir no Kanban: {link}\n"
        )
        return tipo, subject, html, text

    @staticmethod
    def run_due_date_scan(reference_date=None, dry_run=False):
        """
        Varre os tickets a vencer e envia os avisos pendentes.

        Retorna um resumo com o que foi enviado — usado tanto pelo scheduler
        quanto pelo endpoint manual de disparo.
        """
        if not Config.NOTIFICATIONS_ENABLED:
            return {"status": "disabled", "enviados": 0, "avisos": []}

        hoje = reference_date or NotificationService._today()
        dias_antecedencia = sorted(set(Config.NOTIFY_DAYS_BEFORE), reverse=True)
        if not dias_antecedencia:
            return {"status": "no_thresholds", "enviados": 0, "avisos": []}

        # Janela: do passado (atrasados) até o maior aviso de antecedência
        horizonte = hoje + timedelta(days=max(dias_antecedencia))
        inicio = date(2000, 1, 1) if Config.NOTIFY_OVERDUE else hoje

        tickets = TicketService.get_due_between(inicio, horizonte)
        logger.info("[Notificações] %s ticket(s) na janela de prazo", len(tickets))

        enviados, falhas, avisos = 0, 0, []

        for ticket in tickets:
            try:
                data_fim = date.fromisoformat(ticket["data_fim"])
            except (ValueError, TypeError, KeyError):
                continue

            dias_restantes = (data_fim - hoje).days

            # Só dispara nos marcos configurados (ou uma vez ao estourar o prazo)
            if dias_restantes >= 0 and dias_restantes not in dias_antecedencia:
                continue
            if dias_restantes < 0 and not Config.NOTIFY_OVERDUE:
                continue

            # Atrasado gera UM aviso por prazo, não um por dia de atraso: a
            # chave de dedupe é fixa em -1. Assim, se a varredura falhar por
            # alguns dias, o aviso ainda sai quando ela voltar.
            chave_dias = -1 if dias_restantes < 0 else dias_restantes

            for recipient in NotificationService._recipients(ticket):
                tipo, subject, html, text = NotificationService._build_email(
                    ticket, recipient, dias_restantes, data_fim
                )

                if dry_run:
                    avisos.append({
                        "ticket": ticket["titulo"], "para": recipient["email"],
                        "tipo": tipo, "dias_restantes": dias_restantes, "enviado": False,
                    })
                    continue

                log_id = NotificationService._claim(
                    ticket, recipient, tipo, data_fim, chave_dias
                )
                if not log_id:
                    continue  # já avisado

                if EmailService.send(recipient["email"], subject, html, text):
                    enviados += 1
                    avisos.append({
                        "ticket": ticket["titulo"], "para": recipient["email"],
                        "tipo": tipo, "dias_restantes": dias_restantes, "enviado": True,
                    })
                else:
                    falhas += 1
                    NotificationService._release(log_id)

        logger.info("[Notificações] %s enviado(s), %s falha(s)", enviados, falhas)
        return {
            "status": "ok",
            "data_referencia": hoje.isoformat(),
            "tickets_analisados": len(tickets),
            "enviados": enviados,
            "falhas": falhas,
            "avisos": avisos,
            "dry_run": dry_run,
        }
