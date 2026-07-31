from flask import Blueprint, request, jsonify, g

from app.middleware.auth import require_auth, require_admin, require_department_manager
from app.services.department_service import DepartmentService

departments_bp = Blueprint("departments", __name__)


@departments_bp.route("/departments", methods=["GET"])
@require_auth
def list_my_departments():
    """Setores visíveis para o usuário logado (admin vê todos)."""
    return jsonify(DepartmentService.get_user_departments(g.user_id, is_admin=g.is_admin))


@departments_bp.route("/departments/all", methods=["GET"])
@require_admin
def list_all_departments():
    """Todos os setores, inclusive inativos (admin)."""
    return jsonify(DepartmentService.get_all(include_inactive=True))


@departments_bp.route("/departments", methods=["POST"])
@require_admin
def create_department():
    data = request.get_json() or {}
    if not data.get("nome"):
        return jsonify({"error": "Campo 'nome' é obrigatório"}), 400

    try:
        department = DepartmentService.create(data)
    except Exception as e:
        return jsonify({"error": f"Falha ao criar setor: {e}"}), 400

    if not department:
        return jsonify({"error": "Falha ao criar setor"}), 500
    return jsonify(department), 201


@departments_bp.route("/departments/<department_id>", methods=["PUT"])
@require_admin
def update_department(department_id):
    data = request.get_json() or {}
    department = DepartmentService.update(department_id, data)
    if not department:
        return jsonify({"error": "Setor não encontrado"}), 404
    return jsonify(department)


@departments_bp.route("/departments/<department_id>", methods=["DELETE"])
@require_admin
def delete_department(department_id):
    DepartmentService.delete(department_id)
    return jsonify({"message": "Setor removido"}), 200


# ─── Membros do setor ───────────────────────────────────────

@departments_bp.route("/departments/<department_id>/members", methods=["POST"])
@require_department_manager
def add_member(department_id):
    data = request.get_json() or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "Campo 'user_id' é obrigatório"}), 400

    member = DepartmentService.add_member(department_id, user_id, data.get("papel", "member"))
    if not member:
        return jsonify({"error": "Falha ao vincular colaborador"}), 500
    return jsonify(member), 201


@departments_bp.route("/departments/<department_id>/members/<user_id>", methods=["DELETE"])
@require_department_manager
def remove_member(department_id, user_id):
    DepartmentService.remove_member(department_id, user_id)
    return jsonify({"message": "Colaborador removido do setor"}), 200
