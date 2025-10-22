import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { draftsAPI } from '../services/api'
import DraftReviewModal from '../components/DraftReviewModal'

export default function Inbox() {
  const queryClient = useQueryClient()
  const [selectedDraft, setSelectedDraft] = useState(null)
  const [statusFilter, setStatusFilter] = useState('pending')

  // Fetch pending drafts
  const { data: drafts, isLoading, error } = useQuery({
    queryKey: ['drafts', statusFilter],
    queryFn: () => statusFilter === 'pending'
      ? draftsAPI.getPending(100)
      : draftsAPI.getAll({ status: statusFilter, limit: 100 }),
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  })

  // Quick approve mutation
  const quickApproveMutation = useMutation({
    mutationFn: (draftId) => draftsAPI.approve(draftId, { action: 'approve' }),
    onSuccess: () => {
      queryClient.invalidateQueries(['drafts'])
    },
  })

  // Quick reject mutation
  const quickRejectMutation = useMutation({
    mutationFn: (draftId) => draftsAPI.approve(draftId, { action: 'reject' }),
    onSuccess: () => {
      queryClient.invalidateQueries(['drafts'])
    },
  })

  const handleQuickApprove = (draft) => {
    if (confirm(`Approve and send email to ${draft.lead?.sender_email}?`)) {
      quickApproveMutation.mutate(draft.id)
    }
  }

  const handleQuickReject = (draft) => {
    if (confirm('Reject this draft?')) {
      quickRejectMutation.mutate(draft.id)
    }
  }

  const getPriorityColor = (priority) => {
    const colors = {
      critical: 'bg-red-100 text-red-800 border-red-300',
      high: 'bg-orange-100 text-orange-800 border-orange-300',
      medium: 'bg-yellow-100 text-yellow-800 border-yellow-300',
      low: 'bg-gray-100 text-gray-800 border-gray-300',
    }
    return colors[priority] || colors.medium
  }

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-blue-100 text-blue-800',
      approved: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      sent: 'bg-purple-100 text-purple-800',
      edited: 'bg-yellow-100 text-yellow-800',
    }
    return colors[status] || colors.pending
  }

  const draftsList = drafts?.data || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Inbox</h1>
          <p className="text-gray-600 mt-1">Review and approve draft email responses</p>
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Filter:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="pending">Pending Review</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="sent">Sent</option>
            <option value="all">All Drafts</option>
          </select>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="text-sm font-medium text-blue-600">Pending Review</div>
          <div className="text-2xl font-bold text-blue-900 mt-1">
            {draftsList.filter(d => d.status === 'pending').length}
          </div>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="text-sm font-medium text-green-600">Approved Today</div>
          <div className="text-2xl font-bold text-green-900 mt-1">
            {draftsList.filter(d => d.status === 'approved' || d.status === 'sent').length}
          </div>
        </div>
        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
          <div className="text-sm font-medium text-purple-600">Sent Today</div>
          <div className="text-2xl font-bold text-purple-900 mt-1">
            {draftsList.filter(d => d.status === 'sent').length}
          </div>
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="text-sm font-medium text-orange-600">Avg Confidence</div>
          <div className="text-2xl font-bold text-orange-900 mt-1">
            {draftsList.length > 0
              ? (draftsList.reduce((sum, d) => sum + (d.confidence_score || 0), 0) / draftsList.length).toFixed(1)
              : '0.0'}
          </div>
        </div>
      </div>

      {/* Drafts List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        {isLoading && (
          <div className="p-8 text-center text-gray-500">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2">Loading drafts...</p>
          </div>
        )}

        {error && (
          <div className="p-8 text-center text-red-600">
            Error loading drafts: {error.message}
          </div>
        )}

        {!isLoading && !error && draftsList.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            <p className="mt-2">No {statusFilter} drafts found</p>
          </div>
        )}

        {!isLoading && !error && draftsList.length > 0 && (
          <div className="divide-y divide-gray-200">
            {draftsList.map((draft) => (
              <div
                key={draft.id}
                className="p-6 hover:bg-gray-50 transition-colors cursor-pointer"
                onClick={() => setSelectedDraft(draft)}
              >
                <div className="flex items-start justify-between">
                  {/* Left: Draft Info */}
                  <div className="flex-1 min-w-0">
                    {/* Header Row */}
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="text-lg font-semibold text-gray-900 truncate">
                        {draft.subject_line}
                      </h3>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(draft.status)}`}>
                        {draft.status}
                      </span>
                      {draft.lead?.response_priority && (
                        <span className={`px-2 py-1 text-xs font-medium rounded border ${getPriorityColor(draft.lead.response_priority)}`}>
                          {draft.lead.response_priority} priority
                        </span>
                      )}
                    </div>

                    {/* Meta Info */}
                    <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                      <div className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                        </svg>
                        <span>{draft.lead?.sender_name || 'Unknown'}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                        </svg>
                        <span>{draft.lead?.sender_email}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span>{new Date(draft.created_at).toLocaleString()}</span>
                      </div>
                    </div>

                    {/* Draft Preview */}
                    <p className="text-gray-700 line-clamp-2 mb-3">
                      {draft.draft_content}
                    </p>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-2">
                      {draft.lead?.product_type?.map((product) => (
                        <span key={product} className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded">
                          {product}
                        </span>
                      ))}
                      {draft.flags?.map((flag) => (
                        <span key={flag} className="px-2 py-1 bg-yellow-50 text-yellow-700 text-xs rounded">
                          ⚠️ {flag.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Right: Actions & Score */}
                  <div className="flex flex-col items-end gap-3 ml-4">
                    {/* Confidence Score */}
                    <div className="text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {(draft.confidence_score || 0).toFixed(1)}
                      </div>
                      <div className="text-xs text-gray-500">Confidence</div>
                    </div>

                    {/* Quick Actions (only for pending) */}
                    {draft.status === 'pending' && (
                      <div className="flex gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleQuickApprove(draft)
                          }}
                          disabled={quickApproveMutation.isPending}
                          className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700 disabled:opacity-50"
                        >
                          ✓ Approve
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            handleQuickReject(draft)
                          }}
                          disabled={quickRejectMutation.isPending}
                          className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:opacity-50"
                        >
                          ✗ Reject
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Draft Review Modal */}
      {selectedDraft && (
        <DraftReviewModal
          draft={selectedDraft}
          onClose={() => setSelectedDraft(null)}
          onUpdate={() => {
            setSelectedDraft(null)
            queryClient.invalidateQueries(['drafts'])
          }}
        />
      )}
    </div>
  )
}
