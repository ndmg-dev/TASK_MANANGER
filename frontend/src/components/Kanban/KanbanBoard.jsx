import { useState } from 'react'
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  pointerWithin,
} from '@dnd-kit/core'
import { sortableKeyboardCoordinates } from '@dnd-kit/sortable'
import KanbanColumn from './KanbanColumn'
import KanbanCard from './KanbanCard'
import CardModal from './CardModal'
import { useTickets } from '../../hooks/useTickets'
import { useDepartments } from '../../contexts/DepartmentContext'
import { HiOutlinePlusCircle, HiOutlineBuildingOffice2 } from 'react-icons/hi2'

export default function KanbanBoard() {
  const { current: department, currentId, loading: loadingDepts } = useDepartments()
  const {
    loading,
    error,
    columns,
    getTicketsByColumn,
    createTicket,
    updateTicket,
    moveTicket,
    deleteTicket,
  } = useTickets(currentId)

  const [activeCard, setActiveCard] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [editingTicket, setEditingTicket] = useState(null)

  const ticketsByColumn = getTicketsByColumn()

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates })
  )

  const findContainer = (id) => {
    // Check if id is a column name
    if (columns.includes(id)) return id
    // Find which column contains this ticket
    for (const col of columns) {
      if (ticketsByColumn[col]?.some(t => t.id === id)) {
        return col
      }
    }
    return null
  }

  const handleDragStart = (event) => {
    const { active } = event
    const ticket = Object.values(ticketsByColumn).flat().find(t => t.id === active.id)
    setActiveCard(ticket)
  }

  const handleDragOver = (event) => {
    // Visual feedback handled by DnD Kit
  }

  const handleDragEnd = (event) => {
    const { active, over } = event
    setActiveCard(null)

    if (!over) return

    const activeContainer = findContainer(active.id)
    let overContainer = findContainer(over.id)

    // If dropped on a column directly
    if (columns.includes(over.id)) {
      overContainer = over.id
    }

    if (!overContainer) return

    if (activeContainer !== overContainer) {
      moveTicket(active.id, overContainer)
    }
  }

  const handleCreateTicket = async (data) => {
    await createTicket(data)
    setModalOpen(false)
  }

  const handleUpdateTicket = async (data) => {
    await updateTicket(editingTicket.id, data)
    setEditingTicket(null)
    setModalOpen(false)
  }

  const handleEditCard = (ticket) => {
    setEditingTicket(ticket)
    setModalOpen(true)
  }

  const handleDeleteCard = async (ticketId) => {
    if (window.confirm('Tem certeza que deseja remover este ticket?')) {
      await deleteTicket(ticketId)
    }
  }

  // Colaborador ainda sem setor vinculado
  if (!loadingDepts && !currentId) {
    return (
      <div style={{ padding: 64, textAlign: 'center', color: 'var(--color-text-muted)' }}>
        <HiOutlineBuildingOffice2 size={44} style={{ opacity: 0.4, marginBottom: 16 }} />
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8, color: 'var(--color-text-primary)' }}>
          Nenhum setor vinculado
        </h2>
        <p style={{ fontSize: 14, maxWidth: 420, margin: '0 auto', lineHeight: 1.6 }}>
          Seu usuário ainda não faz parte de nenhum setor. Peça a um administrador para
          incluir você no Painel Admin → Setores.
        </p>
      </div>
    )
  }

  if (loading || loadingDepts) {
    return (
      <div style={{ padding: 32 }}>
        <div style={{ display: 'flex', gap: 20, overflow: 'auto' }}>
          {columns.map(col => (
            <div key={col} style={{ minWidth: 280 }}>
              <div className="skeleton" style={{ height: 40, marginBottom: 16 }} />
              <div className="skeleton" style={{ height: 100, marginBottom: 8 }} />
              <div className="skeleton" style={{ height: 100, marginBottom: 8 }} />
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <div
        className="glass"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '20px 32px',
          borderTop: 'none',
          borderLeft: 'none',
          borderRight: 'none',
          borderBottom: '1px solid var(--color-border)',
          borderRadius: 0,
          position: 'relative',
        }}
      >
        {/* Gold accent line */}
        <div style={{ position: 'absolute', bottom: 0, left: 32, right: 32, height: 1, background: 'linear-gradient(90deg, rgba(212,168,83,0.2), transparent 80%)' }} />
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h1 style={{ fontSize: 22, fontWeight: 700 }}>Kanban Board</h1>
            {department && (
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 700,
                  letterSpacing: 0.5,
                  padding: '3px 10px',
                  borderRadius: 999,
                  color: department.cor || 'var(--color-accent-gold)',
                  background: `${department.cor || '#d4a853'}1a`,
                  border: `1px solid ${department.cor || '#d4a853'}44`,
                }}
              >
                {department.nome}
              </span>
            )}
          </div>
          <p style={{ fontSize: 13, color: 'var(--color-text-muted)', marginTop: 2 }}>
            {department
              ? `Gerencie as atividades do setor ${department.nome}`
              : 'Gerencie as atividades da sua equipe'}
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => { setEditingTicket(null); setModalOpen(true) }}
          id="btn-new-ticket"
        >
          <HiOutlinePlusCircle size={18} />
          Novo Ticket
        </button>
      </div>

      {error && (
        <div
          style={{
            margin: '16px 32px 0',
            padding: '10px 14px',
            borderRadius: 8,
            fontSize: 13,
            background: 'var(--color-danger-soft)',
            color: 'var(--color-danger)',
          }}
        >
          {error}
        </div>
      )}

      {/* Board */}
      <DndContext
        sensors={sensors}
        collisionDetection={pointerWithin}
        onDragStart={handleDragStart}
        onDragOver={handleDragOver}
        onDragEnd={handleDragEnd}
      >
        <div
          style={{
            display: 'flex',
            gap: 16,
            padding: '20px 32px',
            overflow: 'auto',
            flex: 1,
          }}
        >
          {columns.map(column => (
            <KanbanColumn
              key={column}
              id={column}
              title={column}
              tickets={ticketsByColumn[column] || []}
              onEditCard={handleEditCard}
              onDeleteCard={handleDeleteCard}
            />
          ))}
        </div>

        <DragOverlay>
          {activeCard ? (
            <div className="kanban-card-overlay">
              <div style={{ fontSize: 13, fontWeight: 600 }}>{activeCard.titulo}</div>
              {activeCard.prioridade && (
                <span className={`badge badge-${activeCard.prioridade}`} style={{ marginTop: 8, display: 'inline-block' }}>
                  {activeCard.prioridade}
                </span>
              )}
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>

      {/* Modal */}
      {modalOpen && (
        <CardModal
          ticket={editingTicket}
          departmentId={currentId}
          onSave={editingTicket ? handleUpdateTicket : handleCreateTicket}
          onClose={() => { setModalOpen(false); setEditingTicket(null) }}
        />
      )}
    </div>
  )
}
