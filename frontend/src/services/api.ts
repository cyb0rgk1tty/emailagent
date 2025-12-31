import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import type {
  Lead,
  LeadCreate,
  LeadUpdate,
  LeadStats,
  LeadsQueryParams,
  Draft,
  DraftCreate,
  DraftUpdate,
  DraftApproval,
  DraftStats,
  DraftsQueryParams,
  AnalyticsSummary,
  AnalyticsOverview,
  ProductTypeTrend,
  AnalyticsQueryParams,
  DocumentInfo,
  RAGQuery,
  RAGResponse,
  KnowledgeStats,
  Conversation,
  ConversationWithMessages,
  ConversationTimeline,
  PaginationParams,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

const api: AxiosInstance = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add auth token if available
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// ==================== Leads API ====================

export const leadsAPI = {
  getAll: (params?: LeadsQueryParams): Promise<AxiosResponse<Lead[]>> =>
    api.get('/leads', { params }),

  getById: (id: number): Promise<AxiosResponse<Lead>> =>
    api.get(`/leads/${id}`),

  create: (data: LeadCreate): Promise<AxiosResponse<Lead>> =>
    api.post('/leads', data),

  update: (id: number, data: LeadUpdate): Promise<AxiosResponse<Lead>> =>
    api.put(`/leads/${id}`, data),

  getCount: (): Promise<AxiosResponse<LeadStats>> =>
    api.get('/leads/stats/count'),
};

// ==================== Drafts API ====================

export const draftsAPI = {
  getAll: (params?: DraftsQueryParams): Promise<AxiosResponse<Draft[]>> =>
    api.get('/drafts', { params }),

  getPending: (limit?: number): Promise<AxiosResponse<Draft[]>> =>
    api.get('/drafts/pending', { params: { limit } }),

  getById: (id: number): Promise<AxiosResponse<Draft>> =>
    api.get(`/drafts/${id}`),

  create: (data: DraftCreate): Promise<AxiosResponse<Draft>> =>
    api.post('/drafts', data),

  update: (id: number, data: DraftUpdate): Promise<AxiosResponse<Draft>> =>
    api.put(`/drafts/${id}`, data),

  approve: (id: number, data: DraftApproval): Promise<AxiosResponse<Draft>> =>
    api.post(`/drafts/${id}/approve`, data),

  getCount: (): Promise<AxiosResponse<DraftStats>> =>
    api.get('/drafts/stats/count'),
};

// ==================== Analytics API ====================

export const analyticsAPI = {
  getSummary: (): Promise<AxiosResponse<AnalyticsSummary>> =>
    api.get('/analytics/summary'),

  getOverview: (params?: AnalyticsQueryParams): Promise<AxiosResponse<AnalyticsOverview>> =>
    api.get('/analytics/overview', { params }),

  getProductTrends: (params?: AnalyticsQueryParams): Promise<AxiosResponse<ProductTypeTrend[]>> =>
    api.get('/analytics/product-trends', { params }),

  getProductTypes: (params?: AnalyticsQueryParams): Promise<AxiosResponse<Record<string, number>>> =>
    api.get('/analytics/product-types', { params }),

  export: (format: 'csv' | 'json', params?: AnalyticsQueryParams): Promise<AxiosResponse<Blob>> =>
    api.get(`/analytics/export/${format}`, {
      params,
      responseType: 'blob',
    }),
};

// ==================== Knowledge API ====================

export const knowledgeAPI = {
  getDocuments: (): Promise<AxiosResponse<DocumentInfo[]>> =>
    api.get('/knowledge/documents'),

  upload: (formData: FormData): Promise<AxiosResponse<DocumentInfo>> =>
    api.post('/knowledge/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),

  reindex: (): Promise<AxiosResponse<{ message: string }>> =>
    api.post('/knowledge/reindex'),

  query: (data: RAGQuery): Promise<AxiosResponse<RAGResponse>> =>
    api.post('/knowledge/query', data),

  deleteDocument: (name: string): Promise<AxiosResponse<void>> =>
    api.delete(`/knowledge/documents/${encodeURIComponent(name)}`),

  getStats: (): Promise<AxiosResponse<KnowledgeStats>> =>
    api.get('/knowledge/stats'),
};

// ==================== Conversations API ====================

export const conversationsAPI = {
  getById: (id: number): Promise<AxiosResponse<ConversationWithMessages>> =>
    api.get(`/conversations/${id}`),

  getByLead: (leadId: number): Promise<AxiosResponse<ConversationWithMessages>> =>
    api.get(`/conversations/lead/${leadId}`),

  getTimeline: (leadId: number): Promise<AxiosResponse<ConversationTimeline>> =>
    api.get(`/conversations/lead/${leadId}/timeline`),

  getBySender: (email: string): Promise<AxiosResponse<Conversation[]>> =>
    api.get(`/conversations/sender/${encodeURIComponent(email)}`),

  getAll: (params?: PaginationParams): Promise<AxiosResponse<Conversation[]>> =>
    api.get('/conversations', { params }),
};

// ==================== Emails API ====================

export const emailsAPI = {
  triggerCheck: (): Promise<AxiosResponse<{ message: string; task_id?: string }>> =>
    api.post('/emails/check'),
};

export default api;
