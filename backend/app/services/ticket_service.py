from app.extensions import get_supabase


class TicketService:
    """Service layer for ticket CRUD operations."""

    VALID_STATUSES = ["Backlog", "To Do", "In Progress", "In Review", "Done"]
    VALID_PRIORITIES = ["low", "medium", "high", "critical"]

    @staticmethod
    def get_all(status=None, assignee_id=None):
        sb = get_supabase()
        query = sb.table("tickets").select(
            "*, assignee:users!assignee_id(id, full_name, avatar_url), creator:users!created_by(id, full_name), ticket_participants(users(id, full_name, avatar_url, email)), ticket_attachments(*)"
        ).order("position")

        if status:
            query = query.eq("status", status)
        if assignee_id:
            query = query.eq("assignee_id", assignee_id)

        result = query.execute()
        return result.data

    @staticmethod
    def get_by_id(ticket_id):
        sb = get_supabase()
        result = sb.table("tickets").select(
            "*, assignee:users!assignee_id(id, full_name, avatar_url, email), creator:users!created_by(id, full_name), ticket_participants(users(id, full_name, avatar_url, email)), ticket_attachments(*)"
        ).eq("id", ticket_id).single().execute()
        return result.data

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
        allowed_fields = ["titulo", "descricao", "status", "prioridade", "assignee_id", "position"]
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

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
