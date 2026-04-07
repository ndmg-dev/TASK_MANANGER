import { useState, useEffect, useCallback } from 'react'
import { ticketsApi } from '../lib/api'
import { supabase } from '../lib/supabaseClient'

const COLUMNS = ['Backlog', 'To Do', 'In Progress', 'In Review', 'Done']

export function useTickets() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const fetchTickets = useCallback(async (isSilent = false) => {
    try {
      if (!isSilent) setLoading(true)
      const { data } = await ticketsApi.getAll()
      setTickets(data)
      setError(null)
    } catch (err) {
      if (!isSilent) setError(err.message)
    } finally {
      if (!isSilent) setLoading(false)
    }
  }, [])

  const fetchSingleTicket = useCallback(async (id) => {
    try {
      const { data } = await ticketsApi.getById(id)
      setTickets(prev => {
        const index = prev.findIndex(t => t.id === id)
        if (index !== -1) {
          // Update existing
          return prev.map(t => t.id === id ? data : t)
        } else {
          // Add new
          return [...prev, data]
        }
      })
    } catch (err) {
      console.error('Error fetching single ticket:', err)
    }
  }, [])

  useEffect(() => {
    fetchTickets()

    // ─── Realtime Subscription ──────────────────────────
    const channel = supabase
      .channel('schema-db-changes')
      .on(
        'postgres_changes',
        {
          event: '*', 
          schema: 'public',
          table: 'tickets'
        },
        (payload) => {
          if (payload.eventType === 'INSERT' || payload.eventType === 'UPDATE') {
            // Quando algo muda, buscamos APENAS esse ticket com seus joins (assignee, etc)
            // Isso evita o flicker de recarregar a lista inteira
            fetchSingleTicket(payload.new.id)
          } else if (payload.eventType === 'DELETE') {
            setTickets(prev => prev.filter(t => t.id === payload.old.id))
          }
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [fetchTickets, fetchSingleTicket])

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
