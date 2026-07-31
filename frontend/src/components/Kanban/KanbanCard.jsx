import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import { HiOutlineClock, HiOutlinePencilSquare, HiOutlineTrash, HiOutlineCalendarDays } from 'react-icons/hi2'

const MS_PER_DAY = 1000 * 60 * 60 * 24

/** Status do prazo do ticket a partir de data_fim (nulo quando não há prazo). */
function getDueInfo(ticket) {
  if (!ticket.data_fim) return null

  // Compara em data local pura para não escorregar de dia por fuso
  const [ano, mes, dia] = ticket.data_fim.split('-').map(Number)
  const prazo = new Date(ano, mes - 1, dia)
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)

  const dias = Math.round((prazo - hoje) / MS_PER_DAY)
  const label = prazo.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })

  if (ticket.status === 'Done') {
    return { texto: `Prazo ${label}`, cor: 'var(--color-text-muted)', fundo: 'var(--color-bg-hover)' }
  }
  if (dias < 0) {
    return {
      texto: `Atrasado ${Math.abs(dias)}d — ${label}`,
      cor: 'var(--color-danger)',
      fundo: 'var(--color-danger-soft)',
    }
  }
  if (dias === 0) {
    return { texto: `Vence hoje — ${label}`, cor: 'var(--color-warning)', fundo: 'var(--color-warning-soft)' }
  }
  if (dias <= 3) {
    return { texto: `Vence em ${dias}d — ${label}`, cor: 'var(--color-warning)', fundo: 'var(--color-warning-soft)' }
  }
  return { texto: `Prazo ${label}`, cor: 'var(--color-text-secondary)', fundo: 'var(--color-bg-hover)' }
}

export default function KanbanCard({ ticket, onEdit, onDelete }) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: ticket.id })

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  // Check if ticket is stalled (>48h without update)
  const hoursStalled = ticket.updated_at
    ? (Date.now() - new Date(ticket.updated_at).getTime()) / (1000 * 60 * 60)
    : 0
  const isStalled = hoursStalled > 48 && ticket.status !== 'Done'
  const dueInfo = getDueInfo(ticket)

  return (
    <div
      ref={setNodeRef}
      style={{ ...style, cursor: 'pointer' }}
      {...attributes}
      {...listeners}
      onClick={onEdit}
      className={`kanban-card ${isDragging ? 'dragging' : ''} ${ticket.status === 'Done' ? 'card-done' : ''} animate-fade-in`}
    >
      {/* Stalled indicator */}
      {isStalled && (
        <div className="stalled-indicator" title={`Parado há ${Math.round(hoursStalled)}h`}>
          <HiOutlineClock size={16} />
        </div>
      )}

      {/* Header: ID + Priority */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{
          fontSize: 10,
          fontWeight: 700,
          color: 'var(--color-accent-gold)',
          background: 'rgba(212,168,83,0.1)',
          padding: '2px 6px',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid rgba(212,168,83,0.2)',
          letterSpacing: '0.5px'
        }}>
          NDMG-{ticket.id.substring(0,8)}
        </span>
        <span className={`badge badge-${ticket.prioridade}`}>
          {ticket.prioridade}
        </span>
      </div>

      {/* Title */}
      <h3 style={{ fontSize: 13, fontWeight: 600, lineHeight: 1.4, marginBottom: 8, paddingRight: isStalled ? 24 : 0, display: 'flex', alignItems: 'flex-start', gap: 6 }}>
        {ticket.status === 'Done' && <span style={{ color: 'var(--color-success)', fontSize: 14 }}>✓</span>}
        {ticket.titulo}
      </h3>

      {/* Description preview */}
      {ticket.descricao && (
        <p
          style={{
            fontSize: 12,
            color: 'var(--color-text-secondary)',
            lineHeight: 1.4,
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            marginBottom: 10,
          }}
        >
          {ticket.descricao}
        </p>
      )}

      {/* Prazo */}
      {dueInfo && (
        <div
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 5,
            fontSize: 11,
            fontWeight: 600,
            padding: '3px 8px',
            borderRadius: 999,
            marginBottom: 10,
            color: dueInfo.cor,
            background: dueInfo.fundo,
          }}
          title={
            ticket.data_inicio
              ? `Início: ${ticket.data_inicio.split('-').reverse().join('/')}`
              : 'Sem data de início'
          }
        >
          <HiOutlineCalendarDays size={12} />
          {dueInfo.texto}
        </div>
      )}

      {/* Footer */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          paddingTop: 8,
          borderTop: '1px solid var(--color-border)',
        }}
      >
        {/* Assignee & Participants */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          {/* Main Assignee */}
          <div style={{ display: 'flex', alignItems: 'center', position: 'relative' }}>
            {ticket.assignee?.avatar_url ? (
              <img
                src={ticket.assignee.avatar_url}
                alt={ticket.assignee.full_name}
                style={{ width: 22, height: 22, borderRadius: '50%', border: '1px solid var(--color-border)' }}
                title={`Responsável: ${ticket.assignee.full_name}`}
              />
            ) : ticket.assignee?.full_name ? (
              <div
                style={{
                  width: 22,
                  height: 22,
                  borderRadius: '50%',
                  background: 'var(--color-bg-active)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: 10,
                  fontWeight: 700,
                  color: 'var(--color-text-secondary)',
                  border: '1px solid var(--color-border)',
                }}
                title={`Responsável: ${ticket.assignee.full_name}`}
              >
                {ticket.assignee.full_name[0]}
              </div>
            ) : null}

            {/* Participants (Overlapping) */}
            {ticket.ticket_participants?.map((p, idx) => (
              <div key={p.users.id} style={{ marginLeft: -6, zIndex: idx + 1 }} title={`Convidado: ${p.users.full_name}`}>
                {p.users.avatar_url ? (
                  <img
                    src={p.users.avatar_url}
                    alt={p.users.full_name}
                    style={{ width: 22, height: 22, borderRadius: '50%', border: '1px solid var(--color-border)' }}
                  />
                ) : (
                  <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'rgba(59, 130, 246, 0.2)', border: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 10, fontWeight: 700, color: '#3b82f6' }}>
                    {p.users.full_name?.[0]}
                  </div>
                )}
              </div>
            ))}
          </div>
          
          <span style={{ fontSize: 11, color: 'var(--color-text-muted)', marginLeft: 4 }}>
            {!ticket.assignee && !ticket.ticket_participants?.length ? 'Sem responsável' : ''}
          </span>
          
          {/* Checklist Indicator */}
          {ticket.ticket_checklists?.length > 0 && (
            <span 
              style={{ 
                fontSize: 10, padding: '2px 6px', background: 'rgba(34, 197, 94, 0.1)', 
                color: 'var(--color-success)', borderRadius: 12, marginLeft: 4, 
                display: 'flex', alignItems: 'center', gap: 4, border: '1px solid rgba(34, 197, 94, 0.2)' 
              }}
              title="Progresso do Checklist"
            >
              ☑️ {ticket.ticket_checklists.filter(i => i.completed).length}/{ticket.ticket_checklists.length}
            </span>
          )}

          {/* Attachments Indicator */}
          {ticket.ticket_attachments?.length > 0 && (
            <span style={{ fontSize: 10, padding: '2px 6px', background: 'var(--color-bg-hover)', borderRadius: 12, marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 4 }}>
              📎 {ticket.ticket_attachments.length}
            </span>
          )}
        </div>

        {/* Actions */}
        <div style={{ display: 'flex', gap: 4 }}>
          <button
            onClick={(e) => { e.stopPropagation(); onEdit() }}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              padding: 4,
              borderRadius: 4,
              transition: 'color 0.15s',
              display: 'flex',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-accent-gold)')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-muted)')}
            title="Editar"
          >
            <HiOutlinePencilSquare size={14} />
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete() }}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--color-text-muted)',
              cursor: 'pointer',
              padding: 4,
              borderRadius: 4,
              transition: 'color 0.15s',
              display: 'flex',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-danger)')}
            onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--color-text-muted)')}
            title="Remover"
          >
            <HiOutlineTrash size={14} />
          </button>
        </div>
      </div>

      {/* Stalled bar */}
      {isStalled && (
        <div
          style={{
            marginTop: 8,
            padding: '4px 8px',
            background: 'var(--color-warning-soft)',
            borderRadius: 'var(--radius-sm)',
            fontSize: 11,
            color: 'var(--color-warning)',
            fontWeight: 500,
            display: 'flex',
            alignItems: 'center',
            gap: 4,
          }}
        >
          <HiOutlineClock size={12} />
          Parado há {Math.round(hoursStalled / 24)} dias
        </div>
      )}

      {/* GitHub PR Indicator */}
      {ticket.github_pr && (
        <div style={{ marginTop: 8 }}>
          {ticket.github_pr.status === 'loading' && (
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--color-text-muted)' }}>
              <span style={{ 
                width: 12, height: 12, border: '2px solid var(--color-border)', 
                borderTopColor: 'var(--color-accent-gold)', borderRadius: '50%', 
                animation: 'spin 1s linear infinite' 
              }} />
              <style>{`@keyframes spin { 100% { transform: rotate(360deg); } }`}</style>
              Gerando Code Review (IA)...
            </div>
          )}
          {ticket.github_pr.status === 'created' && (
            <a 
              href={ticket.github_pr.pr_url} 
              target="_blank" 
              rel="noreferrer" 
              onClick={(e) => e.stopPropagation()}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, color: '#f5f0e8', textDecoration: 'none', background: 'var(--color-info)', padding: '4px 8px', borderRadius: 4, fontWeight: 600 }}
            >
              🔗 PR #{ticket.github_pr.pr_number} Gerado
            </a>
          )}
          {ticket.github_pr.status === 'exists' && (
            <a 
              href={ticket.github_pr.pr_url} 
              target="_blank" 
              rel="noreferrer" 
              onClick={(e) => e.stopPropagation()}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 11, color: 'var(--color-text-primary)', textDecoration: 'none', background: 'var(--color-bg-active)', padding: '4px 8px', borderRadius: 4 }}
            >
              🔗 PR #{ticket.github_pr.pr_number} (Existente)
            </a>
          )}
          {ticket.github_pr.status === 'error' && (
            <div style={{ fontSize: 11, color: 'var(--color-danger)' }}>
              ⚠️ Erro no PR: {ticket.github_pr.error || 'Falha ao gerar'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
