import { useState, useEffect, useCallback } from 'react'
import { ticketsApi } from '../lib/api'
import { supabase } from '../lib/supabaseClient'

const COLUMNS = ['Backlog', 'To Do', 'In Progress', 'In Review', 'Done']

export function useTickets() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchTickets = useCallback(async () => {
    try {
      setLoading(true)
      const { data } = await ticketsApi.getAll()
      setTickets(data)
      setError(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchTickets()

    // ─── Realtime Subscription ──────────────────────────
    // Subscreve a mudanças na tabela de tickets para todos os usuários
    const channel = supabase
      .channel('schema-db-changes')
      .on(
        'postgres_changes',
        {
          event: '*', // Listen to INSERT, UPDATE, DELETE
          schema: 'public',
          table: 'tickets'
        },
        () => {
          // Quando algo muda no banco, recarregamos a lista
          // Isso garante que todos vejam o board atualizado "ao vivo"
          fetchTickets()
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [fetchTickets])

  const getTicketsByColumn = useCallback(() => {
    const grouped = {}
    COLUMNS.forEach(col => {
      grouped[col] = tickets
        .filter(t => t.status === col)
        .sort((a, b) => a.position - b.position)
    })
    return grouped
  }, [tickets])

  const createTicket = async (data) => {
    const { data: newTicket } = await ticketsApi.create(data)
    setTickets(prev => [...prev, newTicket])
    return newTicket
  }

  const updateTicket = async (id, data) => {
    const { data: updated } = await ticketsApi.update(id, data)
    setTickets(prev => prev.map(t => t.id === id ? { ...t, ...updated } : t))
    return updated
  }

  const moveTicket = async (id, status, position) => {
    // Optimistic update
    setTickets(prev => prev.map(t =>
      t.id === id ? { ...t, status, position: position ?? t.position } : t
    ))

    try {
      const { data: moved } = await ticketsApi.move(id, { status, position })
      setTickets(prev => prev.map(t => t.id === id ? { ...t, ...moved } : t))
    } catch {
      fetchTickets() // Rollback on error
    }
  }

  const deleteTicket = async (id) => {
    setTickets(prev => prev.filter(t => t.id !== id))
    await ticketsApi.delete(id)
  }

  return {
    tickets,
    loading,
    error,
    columns: COLUMNS,
    getTicketsByColumn,
    fetchTickets,
    createTicket,
    updateTicket,
    moveTicket,
    deleteTicket,
  }
}
