import re

from app.extensions import get_supabase


class DepartmentService:
    """Setores da empresa e vínculo dos colaboradores."""

    VALID_PAPEIS = ["manager", "member"]

    @staticmethod
    def _slugify(nome):
        slug = re.sub(r"[^a-z0-9]+", "-", nome.strip().lower()).strip("-")
        return slug or "setor"

    @staticmethod
    def get_all(include_inactive=False):
        sb = get_supabase()
        query = sb.table("departments").select(
            "*, department_members(papel, users(id, full_name, email, avatar_url))"
        ).order("nome")
        if not include_inactive:
            query = query.eq("ativo", True)
        return query.execute().data or []

    @staticmethod
    def get_by_id(department_id):
        sb = get_supabase()
        result = sb.table("departments").select(
            "*, department_members(papel, users(id, full_name, email, avatar_url))"
        ).eq("id", department_id).single().execute()
        return result.data

    @staticmethod
    def create(data):
        sb = get_supabase()
        nome = data["nome"].strip()
        payload = {
            "nome": nome,
            "slug": data.get("slug") or DepartmentService._slugify(nome),
            "descricao": data.get("descricao"),
            "cor": data.get("cor", "#d4a853"),
        }
        result = sb.table("departments").insert(payload).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def update(department_id, data):
        sb = get_supabase()
        payload = {f: data[f] for f in ("nome", "descricao", "cor", "ativo") if f in data}
        if not payload:
            return DepartmentService.get_by_id(department_id)
        sb.table("departments").update(payload).eq("id", department_id).execute()
        return DepartmentService.get_by_id(department_id)

    @staticmethod
    def delete(department_id):
        sb = get_supabase()
        sb.table("departments").delete().eq("id", department_id).execute()
        return True

    # ─── Membros ────────────────────────────────────────

    @staticmethod
    def add_member(department_id, user_id, papel="member"):
        sb = get_supabase()
        if papel not in DepartmentService.VALID_PAPEIS:
            papel = "member"
        result = sb.table("department_members").upsert(
            {"department_id": department_id, "user_id": user_id, "papel": papel},
            on_conflict="department_id,user_id",
        ).execute()
        return result.data[0] if result.data else None

    @staticmethod
    def remove_member(department_id, user_id):
        sb = get_supabase()
        sb.table("department_members").delete().eq(
            "department_id", department_id
        ).eq("user_id", user_id).execute()
        return True

    @staticmethod
    def set_members(department_id, user_ids, papel="member"):
        """Substitui a lista de membros preservando os gestores informados."""
        sb = get_supabase()
        sb.table("department_members").delete().eq("department_id", department_id).execute()
        if user_ids:
            rows = [
                {"department_id": department_id, "user_id": uid, "papel": papel}
                for uid in user_ids
            ]
            sb.table("department_members").insert(rows).execute()
        return DepartmentService.get_by_id(department_id)

    # ─── Escopo de acesso do usuário ────────────────────

    @staticmethod
    def get_user_memberships(user_id):
        """Retorna [{department_id, papel}] do usuário."""
        sb = get_supabase()
        result = sb.table("department_members").select(
            "department_id, papel, departments(id, nome, slug, cor, ativo)"
        ).eq("user_id", user_id).execute()
        return result.data or []

    @staticmethod
    def get_user_department_ids(user_id):
        return [m["department_id"] for m in DepartmentService.get_user_memberships(user_id)]

    @staticmethod
    def get_user_departments(user_id, is_admin=False):
        """Setores que o usuário enxerga no board (admin enxerga todos)."""
        if is_admin:
            return DepartmentService.get_all()

        memberships = DepartmentService.get_user_memberships(user_id)
        departments = []
        for m in memberships:
            dept = m.get("departments")
            if dept and dept.get("ativo"):
                departments.append({**dept, "papel": m["papel"]})
        return sorted(departments, key=lambda d: d["nome"])

    @staticmethod
    def user_can_access(user_id, department_id, is_admin=False):
        if is_admin:
            return True
        if department_id is None:
            return False
        return department_id in DepartmentService.get_user_department_ids(user_id)

    @staticmethod
    def user_manages(user_id, department_id, is_admin=False):
        if is_admin:
            return True
        if department_id is None:
            return False
        return any(
            m["department_id"] == department_id and m["papel"] == "manager"
            for m in DepartmentService.get_user_memberships(user_id)
        )
