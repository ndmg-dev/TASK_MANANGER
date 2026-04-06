from flask import Blueprint, jsonify
from app.middleware.auth import require_auth
from app.services.metrics_service import MetricsService

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.route("/metrics/throughput", methods=["GET"])
@require_auth
def throughput():
    """Tickets completed per week (last 12 weeks)."""
    data = MetricsService.get_throughput(weeks=12)
    return jsonify(data)


@metrics_bp.route("/metrics/cycle-time", methods=["GET"])
@require_auth
def cycle_time():
    """Average cycle time (In Progress → Done)."""
    data = MetricsService.get_cycle_time()
    return jsonify(data)


@metrics_bp.route("/metrics/lead-time", methods=["GET"])
@require_auth
def lead_time():
    """Average lead time (Created → Done)."""
    data = MetricsService.get_lead_time()
    return jsonify(data)


@metrics_bp.route("/metrics/bottlenecks", methods=["GET"])
@require_auth
def bottlenecks():
    """Identify WIP violations and stalled tickets."""
    data = MetricsService.get_bottlenecks()
    return jsonify(data)
