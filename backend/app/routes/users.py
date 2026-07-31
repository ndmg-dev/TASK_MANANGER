from flask import Blueprint, jsonify, request
from app.middleware.auth import require_auth
from app.extensions import get_supabase

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
@require_auth
def list_users():
    """
    List team members.

    Com ?department_id=... retorna apenas os colaboradores daquele setor —
    é o que alimenta os seletores de responsável e participantes do ticket.
    """
    sb = get_supabase()
    department_id = request.args.get("department_id")

    if department_id:
        members = sb.table("department_members").select(
            "users(id, full_name, email, role, avatar_url)"
        ).eq("department_id", department_id).execute()
        users = [m["users"] for m in (members.data or []) if m.get("users")]
        return jsonify(sorted(users, key=lambda u: u.get("full_name") or ""))

    result = sb.table("users").select(
        "id, full_name, email, role, avatar_url"
    ).order("full_name").execute()
    return jsonify(result.data or [])


@users_bp.route("/users/me", methods=["GET"])
@require_auth
def get_current_user():
    """Get the current authenticated user's profile."""
    from flask import g
    sb = get_supabase()
    result = sb.table("users").select("*").eq("id", g.user_id).single().execute()
    if not result.data:
        return jsonify({"error": "Usuário não encontrado"}), 404
    return jsonify(result.data)
