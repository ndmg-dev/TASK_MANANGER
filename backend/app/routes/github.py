"""
GitHub Integration Routes — NDMG Task Manager

POST /api/github/create-pr        — Manually trigger PR creation for a ticket
POST /api/github/code-review      — Generate AI code review for a branch
GET  /api/github/open-prs         — List open PRs in the repository
GET  /api/github/branch-status    — Check if a branch exists for a ticket
"""

import logging
from flask import Blueprint, request, jsonify
from app.middleware.auth import require_auth
from app.services.github_service import GitHubService
from app.services.ai_service import AIService
from app.services.ticket_service import TicketService

logger = logging.getLogger(__name__)

github_bp = Blueprint("github", __name__)


@github_bp.route("/github/create-pr", methods=["POST"])
@require_auth
def create_pull_request():
    """
    Manually create a PR for a ticket.
    Body: { "ticket_id": "uuid", "include_ai_review": true }
    """
    data = request.get_json()
    ticket_id = data.get("ticket_id")

    if not ticket_id:
        return jsonify({"error": "ticket_id é obrigatório"}), 400

    # Fetch full ticket data
    ticket = TicketService.get_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket não encontrado"}), 404

    include_ai = data.get("include_ai_review", True)
    ai_summary = None

    if include_ai:
        try:
            branch_name = GitHubService.derive_branch_name(ticket)
            diff_data = GitHubService.get_branch_diff(branch_name)
            if diff_data:
                ai_summary = AIService.generate_code_review_summary(ticket, diff_data)
        except Exception as e:
            logger.warning(f"AI review falhou (pr será criado sem review): {e}")

    result = GitHubService.create_pull_request(ticket, ai_summary=ai_summary)
    return jsonify(result)


@github_bp.route("/github/code-review", methods=["POST"])
@require_auth
def code_review_summary():
    """
    Generate AI code review summary for a ticket's branch.
    Body: { "ticket_id": "uuid" }
    """
    data = request.get_json()
    ticket_id = data.get("ticket_id")

    if not ticket_id:
        return jsonify({"error": "ticket_id é obrigatório"}), 400

    ticket = TicketService.get_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket não encontrado"}), 404

    branch_name = GitHubService.derive_branch_name(ticket)

    # Check if branch exists
    if not GitHubService.branch_exists(branch_name):
        return jsonify({
            "error": f"Branch '{branch_name}' não encontrada no repositório.",
            "expected_branch": branch_name,
        }), 404

    # Get diff
    diff_data = GitHubService.get_branch_diff(branch_name)
    if not diff_data:
        return jsonify({
            "error": "Não foi possível obter o diff da branch.",
        }), 500

    # Generate AI review
    try:
        summary = AIService.generate_code_review_summary(ticket, diff_data)
        return jsonify({
            "review": summary,
            "branch": branch_name,
            "files_changed": len(diff_data.get("files", [])),
            "total_commits": diff_data.get("total_commits", 0),
        })
    except Exception as e:
        return jsonify({
            "error": "Erro ao gerar code review via IA",
            "detail": str(e),
        }), 500


@github_bp.route("/github/open-prs", methods=["GET"])
@require_auth
def list_open_prs():
    """List all open PRs in the configured repository."""
    prs = GitHubService.get_open_prs()
    return jsonify(prs)


@github_bp.route("/github/branch-status/<ticket_id>", methods=["GET"])
@require_auth
def branch_status(ticket_id):
    """Check if a feature branch exists for a given ticket."""
    ticket = TicketService.get_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket não encontrado"}), 404

    branch_name = GitHubService.derive_branch_name(ticket)
    exists = GitHubService.branch_exists(branch_name)

    return jsonify({
        "branch": branch_name,
        "exists": exists,
        "ticket_id": ticket_id,
    })
