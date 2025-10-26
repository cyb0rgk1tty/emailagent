import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { draftsAPI } from '../../services/api'
import ExtractedLeadDataSection from './ExtractedLeadDataSection'
import OriginalInquirySection from './OriginalInquirySection'
import DraftResponseSection from './DraftResponseSection'
import ConfirmModal from '../ConfirmModal'
import toast from 'react-hot-toast'

export default function DraftDetailView({ draft }) {
  const queryClient = useQueryClient()
  const [isEditMode, setIsEditMode] = useState(false)
  const [editedSubject, setEditedSubject] = useState(draft.subject_line)
  const [editedContent, setEditedContent] = useState(draft.draft_content)
  const [editSummary, setEditSummary] = useState('')
  const [confirmModal, setConfirmModal] = useState({ isOpen: false, type: null })

  // Approve/Reject mutation
  const approveMutation = useMutation({
    mutationFn: (data) => draftsAPI.approve(draft.id, data),
    onSuccess: () => {
      queryClient.invalidateQueries(['drafts'])
      setIsEditMode(false)
    },
  })

  // Save edits mutation
  const saveEditsMutation = useMutation({
    mutationFn: () => draftsAPI.approve(draft.id, {
      action: 'save',
      edited_subject: editedSubject,
      edited_content: editedContent,
      feedback: editSummary,
      reviewed_by: 'user',
    }),
    onSuccess: () => {
      queryClient.invalidateQueries(['drafts'])
      setIsEditMode(false)
      setEditSummary('')
    },
  })

  const handleApprove = () => {
    setConfirmModal({ isOpen: true, type: 'approve' })
  }

  const handleReject = () => {
    setConfirmModal({ isOpen: true, type: 'reject' })
  }

  const handleSkip = () => {
    setConfirmModal({ isOpen: true, type: 'skip' })
  }

  const handleConfirmApprove = () => {
    approveMutation.mutate({ action: 'approve', reviewed_by: 'user' })
    setConfirmModal({ isOpen: false, type: null })
  }

  const handleConfirmReject = () => {
    approveMutation.mutate({ action: 'reject', reviewed_by: 'user' })
    setConfirmModal({ isOpen: false, type: null })
  }

  const handleConfirmSkip = () => {
    approveMutation.mutate({ action: 'skip', reviewed_by: 'user' })
    setConfirmModal({ isOpen: false, type: null })
  }

  const handleConfirmDiscard = () => {
    setIsEditMode(false)
    setEditedSubject(draft.subject_line)
    setEditedContent(draft.draft_content)
    setEditSummary('')
    setConfirmModal({ isOpen: false, type: null })
  }

  const handleEdit = () => {
    if (isEditMode) {
      // Cancel edit mode
      if (editedSubject !== draft.subject_line || editedContent !== draft.draft_content) {
        setConfirmModal({ isOpen: true, type: 'discard' })
        return
      }
      setIsEditMode(false)
      setEditedSubject(draft.subject_line)
      setEditedContent(draft.draft_content)
      setEditSummary('')
    } else {
      // Enter edit mode
      setIsEditMode(true)
    }
  }

  const handleSaveEdits = () => {
    if (!editSummary.trim()) {
      toast.error('Please provide a summary of your edits')
      return
    }
    saveEditsMutation.mutate()
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
      skipped: 'bg-gray-100 text-gray-800',
      edited: 'bg-yellow-100 text-yellow-800',
    }
    return colors[status] || colors.pending
  }

  return (
    <div className="flex flex-col h-full">
      {/* Sticky Action Bar */}
      <div className="sticky top-0 z-10 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-8 py-4">
          {/* Left: Metadata */}
          <div className="flex items-center gap-3">
            <span className={`px-2.5 py-1 text-xs font-medium rounded ${getStatusColor(draft.status)}`}>
              {draft.status}
            </span>
            {draft.lead?.response_priority && (
              <span className={`px-2.5 py-1 text-xs font-medium rounded border ${getPriorityColor(draft.lead.response_priority)}`}>
                {draft.lead.response_priority} priority
              </span>
            )}
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Confidence: <span className="font-semibold">{(draft.confidence_score || 0).toFixed(1)}</span>/10</span>
            </div>
          </div>

          {/* Right: Actions */}
          {draft.status === 'pending' && (
            <div className="flex items-center gap-2">
              {isEditMode ? (
                <>
                  <button
                    onClick={handleEdit}
                    className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSaveEdits}
                    disabled={saveEditsMutation.isPending}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-semibold"
                  >
                    {saveEditsMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleEdit}
                    className="px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors font-medium"
                  >
                    <span className="flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
                      </svg>
                      Edit
                    </span>
                  </button>
                  <button
                    onClick={handleSkip}
                    disabled={approveMutation.isPending}
                    className="px-4 py-2 bg-gray-100 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors font-medium"
                  >
                    <span className="flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 9l3 3m0 0l-3 3m3-3H8m13 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      Skip (Already Handled)
                    </span>
                  </button>
                  <button
                    onClick={handleReject}
                    disabled={approveMutation.isPending}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 transition-colors font-medium"
                  >
                    <span className="flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                      Reject
                    </span>
                  </button>
                  <button
                    onClick={handleApprove}
                    disabled={approveMutation.isPending}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors font-semibold"
                  >
                    {approveMutation.isPending ? (
                      'Sending...'
                    ) : (
                      <span className="flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                        Approve & Send
                      </span>
                    )}
                  </button>
                </>
              )}
            </div>
          )}

          {draft.status !== 'pending' && (
            <div className="text-sm text-gray-500">
              {draft.status === 'sent' && 'This draft has been sent'}
              {draft.status === 'approved' && 'This draft has been approved'}
              {draft.status === 'rejected' && 'This draft was rejected'}
              {draft.status === 'skipped' && 'This draft was skipped (already handled manually)'}
            </div>
          )}
        </div>
      </div>

      {/* Scrollable Content */}
      <div className="flex-1 overflow-y-auto p-8 space-y-8 max-w-6xl mx-auto w-full">
        {/* Subject Line Header */}
        <div className="border-b border-gray-200 pb-6">
          <div className="flex items-start gap-3">
            <svg className="w-6 h-6 text-gray-400 flex-shrink-0 mt-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
            <div className="flex-1 min-w-0">
              <h1 className="text-2xl font-bold text-gray-900 break-words">
                {draft.subject_line}
              </h1>
              <p className="text-sm text-gray-500 mt-2">
                Draft created {new Date(draft.created_at).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Extracted Lead Intelligence */}
        <ExtractedLeadDataSection lead={draft.lead} />

        {/* Original Inquiry Section */}
        <OriginalInquirySection lead={draft.lead} />

        {/* Draft Response Section */}
        <DraftResponseSection
          draft={draft}
          isEditMode={isEditMode}
          editedSubject={editedSubject}
          setEditedSubject={setEditedSubject}
          editedContent={editedContent}
          setEditedContent={setEditedContent}
          editSummary={editSummary}
          setEditSummary={setEditSummary}
        />
      </div>

      {/* Confirmation Modals */}
      <ConfirmModal
        isOpen={confirmModal.isOpen && confirmModal.type === 'approve'}
        onClose={() => setConfirmModal({ isOpen: false, type: null })}
        onConfirm={handleConfirmApprove}
        title="Send Email"
        message={`Send this email to ${draft.lead?.sender_email}?`}
        confirmText="Send Email"
        cancelText="Cancel"
        variant="success"
        loading={approveMutation.isPending}
      />

      <ConfirmModal
        isOpen={confirmModal.isOpen && confirmModal.type === 'reject'}
        onClose={() => setConfirmModal({ isOpen: false, type: null })}
        onConfirm={handleConfirmReject}
        title="Reject Draft"
        message="Are you sure you want to reject this draft? This action cannot be undone."
        confirmText="Reject Draft"
        cancelText="Cancel"
        variant="danger"
        loading={approveMutation.isPending}
      />

      <ConfirmModal
        isOpen={confirmModal.isOpen && confirmModal.type === 'skip'}
        onClose={() => setConfirmModal({ isOpen: false, type: null })}
        onConfirm={handleConfirmSkip}
        title="Skip Draft"
        message="Skip this draft? Use this if you already replied manually to this inquiry."
        confirmText="Skip Draft"
        cancelText="Cancel"
        variant="warning"
        loading={approveMutation.isPending}
      />

      <ConfirmModal
        isOpen={confirmModal.isOpen && confirmModal.type === 'discard'}
        onClose={() => setConfirmModal({ isOpen: false, type: null })}
        onConfirm={handleConfirmDiscard}
        title="Discard Changes"
        message="Are you sure you want to discard your unsaved changes?"
        confirmText="Discard Changes"
        cancelText="Keep Editing"
        variant="warning"
      />
    </div>
  )
}
