import logging
from flask import Blueprint, request, jsonify, g
from app.middleware.auth import require_auth, require_admin
from app.services.ticket_service import TicketService

logger = logging.getLogger(__name__)

tickets_bp = Blueprint("tickets", __name__)


@tickets_bp.route("/tickets", methods=["GET"])
@require_auth
def list_tickets():
    """List all tickets with optional filters."""
    status = request.args.get("status")
    assignee_id = request.args.get("assignee_id")

    tickets = TicketService.get_all(status=status, assignee_id=assignee_id)
    return jsonify(tickets)


@tickets_bp.route("/tickets/<ticket_id>", methods=["GET"])
@require_auth
def get_ticket(ticket_id):
    """Get a single ticket by ID."""
    ticket = TicketService.get_by_id(ticket_id)
    if not ticket:
        return jsonify({"error": "Ticket não encontrado"}), 404
    return jsonify(ticket)


@tickets_bp.route("/tickets", methods=["POST"])
@require_auth
def create_ticket():
    """Create a new ticket."""
    data = request.get_json()

    if not data or not data.get("titulo"):
        return jsonify({"error": "Campo 'titulo' é obrigatório"}), 400

    if data.get("status") and data["status"] not in TicketService.VALID_STATUSES:
        return jsonify({"error": f"Status inválido. Use: {TicketService.VALID_STATUSES}"}), 400

    if data.get("prioridade") and data["prioridade"] not in TicketService.VALID_PRIORITIES:
        return jsonify({"error": f"Prioridade inválida. Use: {TicketService.VALID_PRIORITIES}"}), 400

    ticket = TicketService.create(data, user_id=g.user_id)
    if not ticket:
        return jsonify({"error": "Erro ao criar ticket"}), 500

    return jsonify(ticket), 201


@tickets_bp.route("/tickets/<ticket_id>", methods=["PUT"])
@require_auth
def update_ticket(ticket_id):
    """Update a ticket."""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Corpo da requisição vazio"}), 400

    if data.get("status") and data["status"] not in TicketService.VALID_STATUSES:
        return jsonify({"error": f"Status inválido. Use: {TicketService.VALID_STATUSES}"}), 400

    ticket = TicketService.update(ticket_id, data)
    if not ticket:
        return jsonify({"error": "Ticket não encontrado"}), 404

    return jsonify(ticket)


@tickets_bp.route("/tickets/<ticket_id>/move", methods=["PATCH"])
@require_auth
def move_ticket(ticket_id):
    """
    Move a ticket to a new column (status) and optionally reorder.
    
    REGRA DE NEGÓCIO CRÍTICA: When moving to "Done", automatically triggers
    GitHub PR creation with AI-powered code review summary.
    """
    data = request.get_json()
    new_status = data.get("status")
    new_position = data.get("position")

    if not new_status or new_status not in TicketService.VALID_STATUSES:
        return jsonify({"error": f"Status inválido. Use: {TicketService.VALID_STATUSES}"}), 400

    # Get previous status for transition detection
    previous_ticket = TicketService.get_by_id(ticket_id)
    previous_status = previous_ticket.get("status") if previous_ticket else None

    # Execute the move
    ticket = TicketService.move(ticket_id, new_status, new_position)
    if not ticket:
        return jsonify({"error": "Ticket não encontrado"}), 404

    response = dict(ticket)
    response["github_pr"] = None

    # ── GitHub Automation: Trigger PR on "Done" ──────────────────────
    if new_status == "Done" and previous_status != "Done":
        pr_result = _trigger_github_pr_sync(ticket_id)
        response["github_pr"] = pr_result

    return jsonify(response)


def _trigger_github_pr_sync(ticket_id):
    """
    Trigger GitHub PR creation synchronously to return the URL.
    """
    try:
        from app.services.github_service import GitHubService
        from app.services.ai_service import AIService

        # Refetch full ticket with relations
        full_ticket = TicketService.get_by_id(ticket_id)
        if not full_ticket:
            logger.error(f"Ticket {ticket_id} não encontrado para PR automático")
            return {"status": "error", "error": "Ticket não encontrado"}

        branch_name = GitHubService.derive_branch_name(full_ticket)
        logger.info(f"[GitHub Auto-PR] Ticket {ticket_id} → Done. Branch: {branch_name}")

        # Check if branch exists before doing anything
        if not GitHubService.branch_exists(branch_name):
            logger.info(
                f"[GitHub Auto-PR] Branch {branch_name} não existe. "
                f"PR não será criado para ticket {ticket_id}."
            )
            return {"status": "skipped", "message": "Branch não existe."}

        # Get diff and generate AI code review
        ai_summary = None
        try:
            diff_data = GitHubService.get_branch_diff(branch_name)
            if diff_data:
                ai_summary = AIService.generate_code_review_summary(
                    full_ticket, diff_data
                )
                logger.info(f"[GitHub Auto-PR] Code review IA gerado para {branch_name}")
        except Exception as e:
            logger.warning(f"[GitHub Auto-PR] Falha ao gerar code review IA: {e}")

        # Create PR
        result = GitHubService.create_pull_request(full_ticket, ai_summary=ai_summary)
        logger.info(f"[GitHub Auto-PR] Resultado: {result.get('status')} — {result}")
        return result

    except Exception as e:
        logger.error(f"[GitHub Auto-PR] Erro fatal: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@tickets_bp.route("/tickets/<ticket_id>", methods=["DELETE"])
@require_admin
def delete_ticket(ticket_id):
    """Delete a ticket (admin only)."""
    TicketService.delete(ticket_id)
    return jsonify({"message": "Ticket removido com sucesso"}), 200


@tickets_bp.route("/tickets/reorder", methods=["POST"])
@require_auth
def reorder_tickets():
    """Reorder tickets within a column."""
    data = request.get_json()
    status = data.get("status")
    ticket_ids = data.get("ticket_ids", [])

    if not status or not ticket_ids:
        return jsonify({"error": "status e ticket_ids são obrigatórios"}), 400

    TicketService.reorder_column(status, ticket_ids)
    return jsonify({"message": "Ordem atualizada"})
