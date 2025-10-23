import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// API methods
export const leadsAPI = {
  getAll: (params) => api.get('/leads', { params }),
  getById: (id) => api.get(`/leads/${id}`),
  create: (data) => api.post('/leads', data),
  update: (id, data) => api.put(`/leads/${id}`, data),
  getCount: () => api.get('/leads/stats/count'),
}

export const draftsAPI = {
  getAll: (params) => api.get('/drafts', { params }),
  getPending: (limit) => api.get('/drafts/pending', { params: { limit } }),
  getById: (id) => api.get(`/drafts/${id}`),
  create: (data) => api.post('/drafts', data),
  update: (id, data) => api.put(`/drafts/${id}`, data),
  approve: (id, data) => api.post(`/drafts/${id}/approve`, data),
  getCount: () => api.get('/drafts/stats/count'),
}

export const analyticsAPI = {
  getSummary: () => api.get('/analytics/summary'),
  getOverview: (params) => api.get('/analytics/overview', { params }),
  getProductTrends: (params) => api.get('/analytics/product-trends', { params }),
  export: (format, params) => api.get(`/analytics/export/${format}`, {
    params,
    responseType: 'blob'
  }),
}

export const knowledgeAPI = {
  getDocuments: () => api.get('/knowledge/documents'),
  upload: (formData) => api.post('/knowledge/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  reindex: () => api.post('/knowledge/reindex'),
  query: (data) => api.post('/knowledge/query', data),
  deleteDocument: (name) => api.delete(`/knowledge/documents/${name}`),
  getStats: () => api.get('/knowledge/stats'),
}

export const conversationsAPI = {
  getById: (id) => api.get(`/conversations/${id}`),
  getByLead: (leadId) => api.get(`/conversations/lead/${leadId}`),
  getTimeline: (leadId) => api.get(`/conversations/lead/${leadId}/timeline`),
  getBySender: (email) => api.get(`/conversations/sender/${email}`),
  getAll: (params) => api.get('/conversations', { params }),
}

export default api
