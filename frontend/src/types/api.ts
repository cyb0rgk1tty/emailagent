/**
 * API Type Definitions for EmailAgent Frontend
 * These types mirror the backend Pydantic schemas
 */

// ==================== Enums ====================

export enum DraftStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EDITED = 'edited',
  SKIPPED = 'skipped',
  SENT = 'sent',
}

export enum LeadStatus {
  NEW = 'new',
  RESPONDED = 'responded',
  CUSTOMER_REPLIED = 'customer_replied',
  CLOSED = 'closed',
  SPAM = 'spam',
}

export enum DraftApprovalAction {
  APPROVE = 'approve',
  REJECT = 'reject',
  EDIT = 'edit',
  SAVE = 'save',
  SKIP = 'skip',
}

// ==================== Lead Types ====================

export interface Lead {
  id: number;
  message_id: string;
  sender_email: string;
  sender_name?: string;
  company_name?: string;
  phone?: string;
  subject?: string;
  body?: string;
  received_at: string;
  processed_at?: string;

  // Thread tracking
  conversation_id?: number;
  parent_lead_id?: number;
  is_duplicate: boolean;
  duplicate_of_lead_id?: number;
  lead_status: LeadStatus | string;

  // Extracted data
  product_type?: string[];
  specific_ingredients?: string[];
  delivery_format?: string[];
  certifications_requested?: string[];

  // Business intelligence
  estimated_quantity?: string;
  timeline_urgency?: string;
  budget_indicator?: string;
  experience_level?: string;
  distribution_channel?: string[];
  has_existing_brand?: boolean;

  // Lead scoring
  lead_quality_score?: number;
  response_priority?: string;

  // Metadata
  specific_questions?: string[];
  geographic_region?: string;
  extraction_confidence?: number;
  internal_notes?: string;

  created_at: string;
  updated_at: string;
}

export interface LeadCreate {
  sender_email: string;
  sender_name?: string;
  company_name?: string;
  phone?: string;
  subject?: string;
  body?: string;
  message_id: string;
  received_at: string;
}

export interface LeadUpdate {
  internal_notes?: string;
  lead_quality_score?: number;
  response_priority?: string;
}

export interface LeadStats {
  total: number;
  new: number;
  responded: number;
  pending_response: number;
}

// ==================== Draft Types ====================

export interface Draft {
  id: number;
  lead_id: number;
  subject_line: string;
  draft_content: string;
  status: DraftStatus | string;
  response_type?: string;
  confidence_score?: number;
  flags: string[];
  rag_sources: string[];

  created_at: string;
  reviewed_at?: string;
  approved_at?: string;
  sent_at?: string;

  reviewed_by?: string;
  approval_feedback?: string;
  edit_summary?: string;

  customer_replied?: boolean;
  customer_sentiment?: string;

  // Relationship
  lead?: Lead;
}

export interface DraftCreate {
  lead_id: number;
  subject_line: string;
  draft_content: string;
  response_type?: string;
  confidence_score?: number;
  flags?: string[];
  rag_sources?: string[];
}

export interface DraftUpdate {
  subject_line?: string;
  draft_content?: string;
  status?: string;
  approval_feedback?: string;
  edit_summary?: string;
}

export interface DraftApproval {
  action: 'approve' | 'reject' | 'edit' | 'save' | 'skip';
  feedback?: string;
  edited_content?: string;
  edited_subject?: string;
  reviewed_by: string;
}

export interface DraftStats {
  total?: number;
  pending?: number;
  approved?: number;
  sent?: number;
  total_drafts?: number;
  pending_drafts?: number;
  approved_drafts?: number;
  rejected_drafts?: number;
}

// ==================== Analytics Types ====================

export interface ProductTypeTrend {
  product_type: string;
  date: string;
  mention_count: number;
  lead_count: number;
  avg_quality_score?: number;
}

export interface AnalyticsOverview {
  total_leads: number;
  total_drafts: number;
  pending_drafts: number;
  avg_quality_score: number;
  approval_rate: number;
  leads_by_priority: Record<string, number>;
  leads_by_product_type: Record<string, number>;
  recent_activity: Array<Record<string, unknown>>;
}

export interface AnalyticsSummary {
  total_leads: number;
  leads_today: number;
  leads_this_week: number;
  pending_drafts: number;
  sent_drafts: number;
  avg_quality_score: number;
  approval_rate: number;
  top_products: Array<{ name: string; count: number }>;
}

export interface AnalyticsTrends {
  product_trends: ProductTypeTrend[];
  certification_trends: Record<string, number>;
  ingredient_trends: Record<string, number>;
  quality_distribution: Record<number, number>;
}

// ==================== Knowledge Base Types ====================

export interface DocumentInfo {
  document_name: string;
  document_type: string;
  chunk_count: number;
  version: number;
  last_updated: string;
  is_active: boolean;
}

export interface DocumentEmbedding {
  id: number;
  document_name: string;
  document_type: string;
  section_title?: string;
  chunk_text: string;
  chunk_index?: number;
  is_active: boolean;
  version: number;
  created_at: string;
}

export interface RAGQuery {
  query: string;
  top_k?: number;
  document_types?: string[];
  min_similarity?: number;
}

export interface RAGResult {
  chunk_text: string;
  content?: string;
  document_name: string;
  document_type: string;
  section_title?: string;
  similarity_score: number;
  metadata?: Record<string, unknown>;
}

export interface RAGResponse {
  query: string;
  results: RAGResult[];
  total_results: number;
}

export interface KnowledgeStats {
  total_documents: number;
  total_chunks: number;
  documents_by_type: Record<string, number>;
}

// ==================== Conversation Types ====================

export interface Conversation {
  id: number;
  thread_subject: string;
  participants: string[];
  initial_message_id: string;
  last_message_id?: string;
  started_at: string;
  last_activity_at: string;
  created_at: string;
  updated_at: string;
}

export interface EmailMessage {
  id: number;
  message_id: string;
  conversation_id: number;
  lead_id?: number;
  direction: 'inbound' | 'outbound';
  message_type: string;
  email_headers?: Record<string, unknown>;
  sender_email: string;
  sender_name?: string;
  recipient_email?: string;
  recipient_name?: string;
  subject?: string;
  body: string;
  is_draft_sent: boolean;
  draft_id?: number;
  sent_at?: string;
  received_at?: string;
  created_at: string;
}

export interface ConversationWithMessages {
  conversation: Conversation;
  messages: EmailMessage[];
  total_messages: number;
  lead_info?: Record<string, unknown>;
}

export interface TimelineEvent {
  event_type: string;
  timestamp: string;
  description?: string;
  email_subject?: string;
  email_body?: string;
}

export interface ConversationTimeline {
  conversation_id: number;
  lead_id: number;
  thread_subject: string;
  timeline: TimelineEvent[];
  started_at: string;
  last_activity_at: string;
}

// ==================== Pagination Types ====================

export interface PaginationParams {
  page?: number;
  page_size?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// ==================== API Response Types ====================

export interface ApiResponse<T> {
  data: T;
  status: number;
  statusText: string;
}

export interface ApiError {
  message: string;
  detail?: string;
  status?: number;
}

// ==================== Query Parameter Types ====================

export interface LeadsQueryParams extends PaginationParams {
  status?: LeadStatus | string;
  priority?: string;
  product_type?: string;
  date_from?: string;
  date_to?: string;
  search?: string;
  limit?: number;
}

export interface DraftsQueryParams extends PaginationParams {
  status?: DraftStatus | string;
  lead_id?: number;
  limit?: number;
}

export interface AnalyticsQueryParams {
  start_date?: string;
  end_date?: string;
  product_type?: string;
  days?: number;
}

// ==================== Health Check Types ====================

export interface HealthCheckResponse {
  status: string;
  environment: string;
  database: string;
  redis?: string;
  timestamp: string;
}
