from flask import Blueprint, jsonify
from app.middleware.auth import require_auth
from app.extensions import get_supabase

users_bp = Blueprint("users", __name__)


@users_bp.route("/users", methods=["GET"])
@require_auth
def list_users():
    """List all team members."""
    sb = get_supabase()
    result = sb.table("users").select("id, full_name, email, role, avatar_url").order("full_name").execute()
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
