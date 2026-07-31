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
  getAll: (params) => api.get('/users', { params }),
  getMe: () => api.get('/users/me'),
}

// ─── Departments (Setores) ──────────────────────
export const departmentsApi = {
  getMine: () => api.get('/departments'),
  getAll: () => api.get('/departments/all'),
  create: (data) => api.post('/departments', data),
  update: (id, data) => api.put(`/departments/${id}`, data),
  delete: (id) => api.delete(`/departments/${id}`),
  addMember: (id, userId, papel = 'member') =>
    api.post(`/departments/${id}/members`, { user_id: userId, papel }),
  removeMember: (id, userId) => api.delete(`/departments/${id}/members/${userId}`),
}

// ─── Notificações (avisos de prazo) ─────────────
export const notificationsApi = {
  getStatus: () => api.get('/notifications/status'),
  run: (dryRun = false) => api.post('/notifications/run', { dry_run: dryRun }),
}

// ─── Metrics ────────────────────────────────────
export const metricsApi = {
  getThroughput: (params) => api.get('/metrics/throughput', { params }),
  getCycleTime: (params) => api.get('/metrics/cycle-time', { params }),
  getLeadTime: (params) => api.get('/metrics/lead-time', { params }),
  getBottlenecks: (params) => api.get('/metrics/bottlenecks', { params }),
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

// ─── Checklists ──────────────────────────────────
export const checklistsApi = {
  add: (ticketId, text) => api.post(`/tickets/${ticketId}/checklists`, { text }),
  update: (itemId, data) => api.put(`/tickets/checklists/${itemId}`, data),
  delete: (itemId) => api.delete(`/tickets/checklists/${itemId}`),
}

export default api
