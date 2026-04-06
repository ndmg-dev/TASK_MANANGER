import uuid
import mimetypes
from flask import Blueprint, request, jsonify, g
from app.middleware.auth import require_auth
from app.extensions import get_supabase

attachments_bp = Blueprint("attachments", __name__)

@attachments_bp.route("/tickets/<ticket_id>/attachments", methods=["POST"])
@require_auth
def upload_attachment(ticket_id):
    """Uploads an image file to Supabase Storage and records it."""
    if "file" not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Nome de arquivo inválido"}), 400

    sb = get_supabase()
    
    # Valida o ticket
    t_req = sb.table("tickets").select("id").eq("id", ticket_id).single().execute()
    if not t_req.data:
        return jsonify({"error": "Ticket não encontrado"}), 404

    # Prepara o arquivo para storage
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ["jpg", "jpeg", "png", "gif", "webp", "webp"]:
        return jsonify({"error": "Apenas imagens são permitidas"}), 400

    unique_filename = f"{ticket_id}/{uuid.uuid4().hex}.{ext}"
    file_bytes = file.read()
    content_type = mimetypes.guess_type(file.filename)[0] or "application/octet-stream"

    # Envia pro Storage
    bucket_name = "tickets-attachments"
    try:
        sb.storage.from_(bucket_name).upload(
            unique_filename,
            file_bytes,
            {"content-type": content_type}
        )
    except Exception as e:
        return jsonify({"error": f"Erro ao fazer upload no bucket: {str(e)}"}), 500

    # Pega URL publica
    public_url = sb.storage.from_(bucket_name).get_public_url(unique_filename)

    # Registra no BD
    att_data = {
        "ticket_id": ticket_id,
        "file_url": public_url,
        "file_name": file.filename,
        "uploaded_by": g.user_id
    }
    
    att_res = sb.table("ticket_attachments").insert(att_data).execute()
    
    return jsonify(att_res.data[0]) if att_res.data else jsonify({"error": "Falha ao gravar"}), 201

@attachments_bp.route("/tickets/<ticket_id>/attachments/<attachment_id>", methods=["DELETE"])
@require_auth
def delete_attachment(ticket_id, attachment_id):
    """Deletes an attachment from DB and Storage."""
    sb = get_supabase()
    
    att = sb.table("ticket_attachments").select("*").eq("id", attachment_id).eq("ticket_id", ticket_id).single().execute()
    if not att.data:
        return jsonify({"error": "Anexo não encontrado"}), 404
        
    # Check permissions
    if g.user_role != "admin" and att.data.get("uploaded_by") != g.user_id:
        return jsonify({"error": "Sem permissão para excluir este anexo"}), 403

    # Delete BD record
    sb.table("ticket_attachments").delete().eq("id", attachment_id).execute()
    
    # Extraction relative path from public_url (hacky but works since we know the structure)
    url = att.data["file_url"]
    # Tenta descobrir o path do arquivo
    try:
        path = url.split(f"/{'tickets-attachments'}/")[-1]
        sb.storage.from_("tickets-attachments").remove([path])
    except:
        pass # Not critical if BD is deleted

    return jsonify({"message": "Anexo removido"})
