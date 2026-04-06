import axios from 'axios'
import { supabase } from './supabaseClient'

const API_URL = import.meta.env.VITE_API_URL || '/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor to add Supabase JWT to every request
api.interceptors.request.use(async (config) => {
  const { data: { session } } = await supabase.auth.getSession()
  if (session?.access_token) {
    config.headers.Authorization = `Bearer ${session.access_token}`
  }
  return config
})

// ─── Tickets ────────────────────────────────────
export const ticketsApi = {
  getAll: (params) => api.get('/tickets', { params }),
  getById: (id) => api.get(`/tickets/${id}`),
  create: (data) => api.post('/tickets', data),
  update: (id, data) => api.put(`/tickets/${id}`, data),
  move: (id, data) => api.patch(`/tickets/${id}/move`, data),
  delete: (id) => api.delete(`/tickets/${id}`),
  reorder: (data) => api.post('/tickets/reorder', data),
}

// ─── Users ──────────────────────────────────────
export const usersApi = {
  getAll: () => api.get('/users'),
  getMe: () => api.get('/users/me'),
}

// ─── Metrics ────────────────────────────────────
export const metricsApi = {
  getThroughput: () => api.get('/metrics/throughput'),
  getCycleTime: () => api.get('/metrics/cycle-time'),
  getLeadTime: () => api.get('/metrics/lead-time'),
  getBottlenecks: () => api.get('/metrics/bottlenecks'),
}

// ─── AI ─────────────────────────────────────────
export const aiApi = {
  getWeeklyReport: () => api.post('/ai/weekly-report'),
  getCodeReview: (ticketId) => api.post('/github/code-review', { ticket_id: ticketId }),
}

// ─── GitHub ─────────────────────────────────────
export const githubApi = {
  createPR: (ticketId, includeAiReview = true) =>
    api.post('/github/create-pr', { ticket_id: ticketId, include_ai_review: includeAiReview }),
  getOpenPRs: () => api.get('/github/open-prs'),
  getBranchStatus: (ticketId) => api.get(`/github/branch-status/${ticketId}`),
}

// ─── Admin ───────────────────────────────────────
export const adminApi = {
  getUsers: () => api.get('/admin/users'),
  updateUserRole: (id, role) => api.patch(`/admin/users/${id}/role`, { role }),
}

// ─── Attachments ─────────────────────────────────
export const attachmentsApi = {
  upload: (ticketId, file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/tickets/${ticketId}/attachments`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  delete: (ticketId, attachmentId) => api.delete(`/tickets/${ticketId}/attachments/${attachmentId}`),
}

export default api
