import { useState, useEffect } from 'react'
import { usersApi, attachmentsApi } from '../../lib/api'
import { HiOutlineXMark } from 'react-icons/hi2'

const STATUSES = ['Backlog', 'To Do', 'In Progress', 'In Review', 'Done']
const PRIORITIES = ['low', 'medium', 'high', 'critical']

const priorityLabels = {
  low: 'Baixa',
  medium: 'Média',
  high: 'Alta',
  critical: 'Crítica',
}

export default function CardModal({ ticket, onSave, onClose }) {
  const [formData, setFormData] = useState({
    titulo: ticket?.titulo || '',
    descricao: ticket?.descricao || '',
    status: ticket?.status || 'Backlog',
    prioridade: ticket?.prioridade || 'medium',
    assignee_id: ticket?.assignee_id || '',
    participants: ticket?.ticket_participants?.map(p => p.users.id) || [],
  })
  const [attachments, setAttachments] = useState(ticket?.ticket_attachments || [])
  const [uploadingFile, setUploadingFile] = useState(false)
  const [users, setUsers] = useState([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    usersApi.getAll().then(({ data }) => setUsers(data)).catch(() => {})
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!formData.titulo.trim()) return
    setSaving(true)
    try {
      await onSave({
        ...formData,
        assignee_id: formData.assignee_id || null,
      })
    } finally {
      setSaving(false)
    }
  }

  const handleFileUpload = async (e) => {
    const file = e.target.files?.[0]
    if (!file || !ticket) return
    
    setUploadingFile(true)
    try {
      const { data } = await attachmentsApi.upload(ticket.id, file)
      if (data) {
        setAttachments(prev => [...prev, data])
      }
    } catch (err) {
      alert("Falha ao enviar imagem. Verifique se o bucket existe.")
    } finally {
      setUploadingFile(false)
    }
  }

  const handleChange = (field) => (e) => {
    setFormData(prev => ({ ...prev, [field]: e.target.value }))
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content animate-fade-in" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: 28,
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <h2 style={{ fontSize: 18, fontWeight: 700, margin: 0 }}>
              {ticket ? 'Editar Ticket' : 'Novo Ticket'}
            </h2>
            {ticket && (
              <span style={{
                background: 'rgba(212,168,83,0.1)',
                color: 'var(--color-accent-gold)',
                border: '1px solid rgba(212,168,83,0.3)',
                padding: '2px 8px',
                borderRadius: 'var(--radius-sm)',
                fontSize: 12,
                fontWeight: 600,
                letterSpacing: '0.5px'
              }}>
                NDMG-{ticket.id.substring(0,8)}
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              padding: 4,
              display: 'flex',
            }}
          >
            <HiOutlineXMark size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Título */}
          <div style={{ marginBottom: 20 }}>
            <label htmlFor="field-titulo">Título *</label>
            <input
              id="field-titulo"
              className="input"
              type="text"
              placeholder="Descreva a tarefa..."
              value={formData.titulo}
              onChange={handleChange('titulo')}
              autoFocus
              required
            />
          </div>

          {/* Descrição */}
          <div style={{ marginBottom: 20 }}>
            <label htmlFor="field-descricao">Descrição</label>
            <textarea
              id="field-descricao"
              className="input"
              placeholder="Detalhes adicionais..."
              value={formData.descricao}
              onChange={handleChange('descricao')}
              rows={3}
            />
          </div>

          {/* Status + Prioridade */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            <div>
              <label htmlFor="field-status">Status</label>
              <select
                id="field-status"
                className="input"
                value={formData.status}
                onChange={handleChange('status')}
              >
                {STATUSES.map(s => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
            <div>
              <label htmlFor="field-prioridade">Prioridade</label>
              <select
                id="field-prioridade"
                className="input"
                value={formData.prioridade}
                onChange={handleChange('prioridade')}
              >
                {PRIORITIES.map(p => (
                  <option key={p} value={p}>{priorityLabels[p]}</option>
                ))}
              </select>
            </div>
          </div>

            {/* Assignee aprimorado */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 20 }}>
            <div>
              <label htmlFor="field-assignee">Responsável Principal</label>
              <select
                id="field-assignee"
                className="input"
                value={formData.assignee_id}
                onChange={handleChange('assignee_id')}
              >
                <option value="">Nenhum</option>
                {users.map(u => (
                  <option key={u.id} value={u.id}>{u.full_name}</option>
                ))}
              </select>
            </div>
            
            <div>
              <label>Outros Participantes (Convidados)</label>
              <div 
                style={{ 
                  background: 'rgba(5, 5, 8, 0.6)', border: '1px solid var(--color-border)', borderRadius: 'var(--radius-sm)', 
                  padding: 8, maxHeight: 80, overflowY: 'auto' 
                }}
              >
                {users.map(u => (
                  <div key={u.id} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
                    <input 
                      type="checkbox" 
                      id={`user-${u.id}`}
                      checked={formData.participants.includes(u.id)}
                      onChange={(e) => {
                        const newParts = e.target.checked 
                          ? [...formData.participants, u.id]
                          : formData.participants.filter(id => id !== u.id);
                        setFormData(prev => ({ ...prev, participants: newParts }))
                      }}
                    />
                    <label htmlFor={`user-${u.id}`} style={{ margin: 0, textTransform: 'none', color: 'var(--color-text-primary)' }}>
                      {u.full_name}
                    </label>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Anexos (Somente tickets existentes) */}
          {ticket && (
            <div style={{ marginBottom: 28, padding: 12, background: 'rgba(212,168,83,0.03)', borderRadius: 8, border: '1px dashed var(--color-border-light)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <label style={{ margin: 0 }}>Anexos ({attachments.length})</label>
                <label className="btn-secondary" style={{ padding: '4px 12px', fontSize: 11, cursor: 'pointer' }}>
                  <input type="file" style={{ display: 'none' }} accept="image/*" onChange={handleFileUpload} disabled={uploadingFile} />
                  {uploadingFile ? 'Enviando...' : '+ Anexar Imagem'}
                </label>
              </div>
              
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                {attachments.map(att => (
                  <div key={att.id} style={{ position: 'relative', width: 60, height: 60, borderRadius: 6, overflow: 'hidden', border: '1px solid var(--color-border)' }}>
                    <img src={att.file_url} alt={att.file_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} onClick={() => window.open(att.file_url, '_blank')} />
                  </div>
                ))}
                {!attachments.length && !uploadingFile && <div style={{ fontSize: 11, color: 'var(--color-text-muted)' }}>Nenhum anexo.</div>}
              </div>
            </div>
          )}
          {!ticket && (
            <div style={{ marginBottom: 28, fontSize: 11, color: 'var(--color-text-muted)' }}>
              * Crie o ticket primeiro para poder anexar imagens.
            </div>
          )}

          {/* Actions */}
          <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
            >
              Cancelar
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={saving || uploadingFile || !formData.titulo.trim()}
              style={{ opacity: (saving || uploadingFile) ? 0.6 : 1 }}
            >
              {saving ? 'Salvando...' : ticket ? 'Salvar Alterações' : 'Criar Ticket'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
