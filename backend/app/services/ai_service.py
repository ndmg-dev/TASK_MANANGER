from datetime import datetime, timedelta, timezone
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from app.config import Config
from app.extensions import get_supabase


class AIService:
    """Service for generating AI-powered weekly reports via Groq/Langchain."""

    @staticmethod
    def generate_weekly_report():
        sb = get_supabase()
        now = datetime.now(timezone.utc)
        week_ago = now - timedelta(days=7)

        # Fetch actual real completed tickets this week
        completed_tickets_req = sb.table("tickets").select(
            "id, titulo, prioridade, updated_at"
        ).eq("status", "Done").gte(
            "updated_at", week_ago.isoformat()
        ).execute()

        completed_tickets = completed_tickets_req.data or []
        completed_ids = [t["id"] for t in completed_tickets]

        # Fetch logs ONLY for these completed tickets + active tickets if it's meant to show bottlenecks
        # But the prompt said "buscar apenas os tickets reais com status 'Done' dos últimos 7 dias e seus respectivos logs"
        all_events = []
        if completed_ids:
            events_req = sb.table("ticket_events_log").select(
                "ticket_id, status_anterior, status_novo, timestamp"
            ).in_("ticket_id", completed_ids).gte(
                "timestamp", week_ago.isoformat()
            ).order("timestamp").execute()
            all_events = events_req.data or []

        # Calculate quick metrics
        completed_count = len(completed_tickets)
        completed_titles = [t.get("titulo", "Sem título") for t in completed_tickets]

        # Build transition summary
        transitions = {}
        for ev in all_events:
            key = f"{ev.get('status_anterior', 'Criado')} → {ev['status_novo']}"
            transitions[key] = transitions.get(key, 0) + 1

        # Identify where tickets spent the most time
        transition_text = "\n".join(
            f"  - {k}: {v} ocorrência(s)" for k, v in sorted(
                transitions.items(), key=lambda x: x[1], reverse=True
            )
        )

        completed_text = "\n".join(
            f"  - {t}" for t in completed_titles
        ) if completed_titles else "  Nenhum ticket concluído esta semana."

        # Call Groq via Langchain
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            api_key=Config.GROQ_API_KEY,
        )

        prompt = ChatPromptTemplate.from_template(
            """Você é um analista de produtividade sênior da equipe Núcleo Digital MG,
que atende a Mendonça Galvão Contadores Associados.

Analise os dados da semana e gere um **resumo executivo** em português brasileiro.

## Dados da Semana ({start_date} a {end_date})

### Tickets Concluídos ({completed_count} total):
{completed_list}

### Transições de Status:
{transitions}

### Total de Eventos: {total_events}

---

Seu relatório deve conter:
1. **Resumo da Produtividade** — visão geral do desempenho da semana
2. **Gargalos Identificados** — onde a equipe ficou travada (ex: "A maioria das tarefas agarrou na fase de revisão")
3. **Destaques Positivos** — conquistas e pontos fortes
4. **Recomendações** — ações concretas para a próxima semana

Seja direto, objetivo e use dados para embasar suas conclusões.
Formate em Markdown."""
        )

        chain = prompt | llm

        result = chain.invoke({
            "start_date": week_ago.strftime("%d/%m/%Y"),
            "end_date": now.strftime("%d/%m/%Y"),
            "completed_count": completed_count,
            "completed_list": completed_text,
            "transitions": transition_text if transition_text else "  Nenhuma transição registrada.",
            "total_events": len(all_events),
        })

        return {
            "report": result.content,
            "metadata": {
                "period_start": week_ago.isoformat(),
                "period_end": now.isoformat(),
                "tickets_completed": completed_count,
                "total_events": len(all_events),
            }
        }

    @staticmethod
    def generate_code_review_summary(ticket, diff_data):
        """
        Generate an AI-powered code review summary for a Pull Request.

        Args:
            ticket: dict with ticket data (titulo, descricao, prioridade)
            diff_data: dict with diff info (files, patch_text, total_commits)

        Returns:
            str: Markdown-formatted code review summary
        """
        if not diff_data or not diff_data.get("patch_text"):
            return (
                "⚠️ _Não foi possível gerar o resumo de code review: "
                "nenhum diff disponível para análise._"
            )

        # Build files summary
        files_table = "\n".join(
            f"  - `{f['filename']}` ({f['status']}) — "
            f"+{f['additions']} / -{f['deletions']}"
            for f in diff_data.get("files", [])
        )

        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.2,
            api_key=Config.GROQ_API_KEY,
        )

        prompt = ChatPromptTemplate.from_template(
            """Você é um Tech Lead sênior fazendo code review para a equipe Núcleo Digital MG.

## Contexto do Ticket
- **Título:** {titulo}
- **Descrição:** {descricao}
- **Prioridade:** {prioridade}

## Alterações ({total_commits} commit(s), {total_files} arquivo(s))
{files_summary}

## Diff (Código Alterado)
{patch}

---

Gere um **resumo de code review** conciso e técnico em português brasileiro:

1. **Visão Geral das Mudanças** — O que foi implementado/alterado (2-3 frases)
2. **Qualidade do Código** — Observações sobre padrões, legibilidade e boas práticas
3. **Riscos Potenciais** — Possíveis problemas (segurança, performance, edge cases)
4. **Recomendações** — Sugestões de melhoria antes do merge (se houver)
5. **Veredito** — ✅ Aprovado / ⚠️ Aprovar com ressalvas / ❌ Solicitar correções

Seja objetivo e direto. Formate em Markdown."""
        )

        # Truncate patch to avoid token limits
        patch_text = diff_data.get("patch_text", "")
        if len(patch_text) > 12000:
            patch_text = patch_text[:12000] + "\n\n... (diff truncado por limite de tokens)"

        chain = prompt | llm

        result = chain.invoke({
            "titulo": ticket.get("titulo", "N/A"),
            "descricao": ticket.get("descricao", "Sem descrição"),
            "prioridade": ticket.get("prioridade", "N/A"),
            "total_commits": diff_data.get("total_commits", 0),
            "total_files": len(diff_data.get("files", [])),
            "files_summary": files_table or "  Nenhum arquivo modificado.",
            "patch": patch_text,
        })

        return result.content

