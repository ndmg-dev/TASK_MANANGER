from app.extensions import get_supabase


class TicketService:
    """Service layer for ticket CRUD operations."""

    VALID_STATUSES = ["Backlog", "To Do", "In Progress", "In Review", "Done"]
    VALID_PRIORITIES = ["low", "medium", "high", "critical"]
    OPEN_STATUSES = ["Backlog", "To Do", "In Progress", "In Review"]

    SELECT_RELATIONS = (
        "*, assignee:users!assignee_id(id, full_name, avatar_url, email), "
        "creator:users!created_by(id, full_name), "
        "department:departments!department_id(id, nome, slug, cor), "
        "ticket_participants(users(id, full_name, avatar_url, email)), "
        "ticket_attachments(*), ticket_checklists(*)"
    )

    @staticmethod
    def get_all(status=None, assignee_id=None, department_id=None, allowed_department_ids=None):
        """
        Lista tickets.

        `allowed_department_ids=None` significa acesso irrestrito (admin).
        Uma lista vazia significa "nenhum setor" e retorna [].
        """
        sb = get_supabase()
        query = sb.table("tickets").select(TicketService.SELECT_RELATIONS).order("position")

        if status:
            query = query.eq("status", status)
        if assignee_id:
            query = query.eq("assignee_id", assignee_id)
        if department_id:
            query = query.eq("department_id", department_id)
        elif allowed_department_ids is not None:
            if not allowed_department_ids:
                return []
            query = query.in_("department_id", allowed_department_ids)

        result = query.execute()
        return result.data

    @staticmethod
    def get_by_id(ticket_id):
        sb = get_supabase()
        result = sb.table("tickets").select(
            TicketService.SELECT_RELATIONS
        ).eq("id", ticket_id).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def create(data, user_id):
        sb = get_supabase()

        # Calculate next position in the target column
        existing = sb.table("tickets").select("position").eq(
            "status", data.get("status", "Backlog")
        ).order("position", desc=True).limit(1).execute()

        next_pos = 0
        if existing.data:
            next_pos = existing.data[0]["position"] + 1

        ticket_data = {
            "titulo": data["titulo"],
            "descricao": data.get("descricao", ""),
            "status": data.get("status", "Backlog"),
            "prioridade": data.get("prioridade", "medium"),
            "assignee_id": data.get("assignee_id"),
            "department_id": data.get("department_id"),
            "data_inicio": data.get("data_inicio") or None,
            "data_fim": data.get("data_fim") or None,
            "created_by": user_id,
            "position": next_pos,
        }

        result = sb.table("tickets").insert(ticket_data).execute()
        ticket = result.data[0] if result.data else None

        if ticket and "participants" in data and isinstance(data["participants"], list):
            parts = [{"ticket_id": ticket["id"], "user_id": uid} for uid in data["participants"]]
            if parts:
                sb.table("ticket_participants").insert(parts).execute()

        # Re-fetch full ticket with joins (assignee, participants, etc.)
        return TicketService.get_by_id(ticket["id"])

    @staticmethod
    def update(ticket_id, data):
        sb = get_supabase()

        update_data = {}
        allowed_fields = [
            "titulo", "descricao", "status", "prioridade", "assignee_id",
            "position", "department_id", "data_inicio", "data_fim",
        ]
        for field in allowed_fields:
            if field in data:
                value = data[field]
                # Inputs de data vazios chegam como "" e violariam o tipo DATE
                if field in ("data_inicio", "data_fim") and not value:
                    value = None
                update_data[field] = value

        if update_data:
            sb.table("tickets").update(update_data).eq("id", ticket_id).execute()

        if "participants" in data and isinstance(data["participants"], list):
            # Deleta os antigos e re-insere
            sb.table("ticket_participants").delete().eq("ticket_id", ticket_id).execute()
            parts = [{"ticket_id": ticket_id, "user_id": uid} for uid in data["participants"]]
            if parts:
                sb.table("ticket_participants").insert(parts).execute()

        return TicketService.get_by_id(ticket_id)

    @staticmethod
    def move(ticket_id, new_status, new_position=None):
        sb = get_supabase()

        update_data = {"status": new_status}
        if new_position is not None:
            update_data["position"] = new_position

        result = sb.table("tickets").update(update_data).eq("id", ticket_id).execute()
        return TicketService.get_by_id(ticket_id) if result.data else None

    @staticmethod
    def delete(ticket_id):
        sb = get_supabase()
        result = sb.table("tickets").delete().eq("id", ticket_id).execute()
        return True

    @staticmethod
    def reorder_column(status, ticket_ids):
        """Reorder tickets within a column based on provided order."""
        sb = get_supabase()
        for idx, tid in enumerate(ticket_ids):
            sb.table("tickets").update({"position": idx}).eq("id", tid).execute()
        return True

    @staticmethod
    def get_due_between(date_from, date_to):
        """
        Tickets em aberto com data de término dentro do intervalo (inclusive).

        Usado pela automação de avisos de prazo.
        """
        sb = get_supabase()
        result = sb.table("tickets").select(
            TicketService.SELECT_RELATIONS
        ).not_.is_("data_fim", "null").gte(
            "data_fim", date_from.isoformat()
        ).lte(
            "data_fim", date_to.isoformat()
        ).in_("status", TicketService.OPEN_STATUSES).execute()
        return result.data or []

    # ─── Checklist Management ───────────────────────────────

    @staticmethod
    def add_checklist_item(ticket_id, text):
        sb = get_supabase()
        # Get next position
        existing = sb.table("ticket_checklists").select("position").eq("ticket_id", ticket_id).order("position", desc=True).limit(1).execute()
        next_pos = (existing.data[0]["position"] + 1) if existing.data else 0
        
        item = {
            "ticket_id": ticket_id,
            "text": text,
            "completed": False,
            "position": next_pos
        }
        result = sb.table("ticket_checklists").insert(item).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def get_checklist_ticket_id(item_id):
        sb = get_supabase()
        result = sb.table("ticket_checklists").select("ticket_id").eq("id", item_id).execute()
        return result.data[0]["ticket_id"] if result.data else None

    @staticmethod
    def update_checklist_item(item_id, data):
        sb = get_supabase()
        update_fields = {}
        for field in ["text", "completed", "position"]:
            if field in data:
                update_fields[field] = data[field]
        
        if update_fields:
            result = sb.table("ticket_checklists").update(update_fields).eq("id", item_id).execute()
            return result.data[0] if result.data else None
        return None

    @staticmethod
    def delete_checklist_item(item_id):
        sb = get_supabase()
        sb.table("ticket_checklists").delete().eq("id", item_id).execute()
        return True
