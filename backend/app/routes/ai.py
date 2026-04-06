from flask import Blueprint, jsonify, request
from app.middleware.auth import require_auth
from app.services.ai_service import AIService

ai_bp = Blueprint("ai", __name__)


@ai_bp.route("/ai/weekly-report", methods=["POST"])
@require_auth
def weekly_report():
    """Generate AI-powered weekly productivity report."""
    try:
        result = AIService.generate_weekly_report()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "error": "Erro ao gerar relatório de IA",
            "detail": str(e),
        }), 500


@ai_bp.route("/ai/code-review-summary", methods=["POST"])
@require_auth
def code_review_summary():
    """
    Generate AI code review summary for a ticket's code changes.
    Body: { "ticket_id": "uuid" }
    Delegates to the /api/github/code-review endpoint logic.
    """
    from app.services.github_service import GitHubService
    from app.services.ticket_service import TicketService

    data = request.get_json()
    ticket_id = data.get("ticket_id")

    if not ticket_id:
        return jsonify({"error": "ticket_id é obrigatório"}), 400

    ticket = TicketService.get_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket não encontrado"}), 404

    branch_name = GitHubService.derive_branch_name(ticket)

    if not GitHubService.branch_exists(branch_name):
        return jsonify({
            "error": f"Branch '{branch_name}' não encontrada.",
            "expected_branch": branch_name,
        }), 404

    diff_data = GitHubService.get_branch_diff(branch_name)
    if not diff_data:
        return jsonify({"error": "Não foi possível obter o diff."}), 500

    try:
        summary = AIService.generate_code_review_summary(ticket, diff_data)
        return jsonify({
            "review": summary,
            "branch": branch_name,
            "files_changed": len(diff_data.get("files", [])),
        })
    except Exception as e:
        return jsonify({
            "error": "Erro ao gerar code review",
            "detail": str(e),
        }), 500
