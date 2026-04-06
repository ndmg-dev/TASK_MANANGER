from flask import Blueprint, jsonify, request
from app.middleware.auth import require_admin
from app.extensions import get_supabase

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/admin/users", methods=["GET"])
@require_admin
def list_users():
    """List all users (Admin only)"""
    sb = get_supabase()
    # Puxar todos da tabela public.users
    result = sb.table("users").select("*").order("created_at").execute()
    return jsonify(result.data or [])

@admin_bp.route("/admin/users/<user_id>/role", methods=["PATCH"])
@require_admin
def update_user_role(user_id):
    """Change a user's role (Admin only)"""
    data = request.get_json()
    new_role = data.get("role")
    
    if new_role not in ["admin", "developer", "viewer"]:
        return jsonify({"error": "Role inválida"}), 400

    sb = get_supabase()
    
    # Atualiza apenas a tabela public.users 
    # (Não atualiza o auth.users metadata, mas o app confia na tabela public prioritarimente)
    result = sb.table("users").update({"role": new_role}).eq("id", user_id).execute()
    
    if not result.data:
        return jsonify({"error": "Usuário não encontrado"}), 404
        
    return jsonify(result.data[0])
