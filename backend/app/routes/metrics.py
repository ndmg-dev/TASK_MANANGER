from flask import Blueprint, jsonify, request, g
from app.middleware.auth import require_auth
from app.services.department_service import DepartmentService
from app.services.metrics_service import MetricsService

metrics_bp = Blueprint("metrics", __name__)


def _scoped_department():
    """
    Setor a considerar nas métricas.

    Sem ?department_id explícito, cai no primeiro setor do usuário — assim o
    Dashboard nunca mistura números de setores diferentes. Admin sem filtro
    enxerga a empresa toda. Retorna (department_id, resposta_de_erro | None).
    """
    department_id = request.args.get("department_id")

    if department_id:
        if not DepartmentService.user_can_access(g.user_id, department_id, is_admin=g.is_admin):
            return None, (jsonify({"error": "Acesso negado a este setor"}), 403)
        return department_id, None

    if g.is_admin:
        return None, None

    meus = DepartmentService.get_user_department_ids(g.user_id)
    if not meus:
        return None, (jsonify({"error": "Usuário sem setor vinculado"}), 403)
    return meus[0], None


@metrics_bp.route("/metrics/throughput", methods=["GET"])
@require_auth
def throughput():
    """Tickets completed per week (last 12 weeks)."""
    department_id, error = _scoped_department()
    if error:
        return error
    return jsonify(MetricsService.get_throughput(weeks=12, department_id=department_id))


@metrics_bp.route("/metrics/cycle-time", methods=["GET"])
@require_auth
def cycle_time():
    """Average cycle time (In Progress → Done)."""
    department_id, error = _scoped_department()
    if error:
        return error
    return jsonify(MetricsService.get_cycle_time(department_id=department_id))


@metrics_bp.route("/metrics/lead-time", methods=["GET"])
@require_auth
def lead_time():
    """Average lead time (Created → Done)."""
    department_id, error = _scoped_department()
    if error:
        return error
    return jsonify(MetricsService.get_lead_time(department_id=department_id))


@metrics_bp.route("/metrics/bottlenecks", methods=["GET"])
@require_auth
def bottlenecks():
    """Identify WIP violations and stalled tickets."""
    department_id, error = _scoped_department()
    if error:
        return error
    return jsonify(MetricsService.get_bottlenecks(department_id=department_id))
