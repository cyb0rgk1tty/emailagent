import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { draftsAPI } from '../services/api'

export default function DraftReviewModal({ draft, onClose, onUpdate }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedSubject, setEditedSubject] = useState(draft.subject_line)
  const [editedContent, setEditedContent] = useState(draft.draft_content)
  const [editSummary, setEditSummary] = useState('')
  const [showFeedback, setShowFeedback] = useState(false)

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (data) => draftsAPI.approve(draft.id, data),
    onSuccess: () => {
      onUpdate()
    },
  })

  // Save edits mutation
  const saveEditsMutation = useMutation({
    mutationFn: (data) => draftsAPI.approve(draft.id, {
      action: 'save',
      edited_subject: editedSubject,
      edited_content: editedContent,
      feedback: editSummary,
      reviewed_by: 'user',
    }),
    onSuccess: () => {
      setIsEditing(false)
      onUpdate()
    },
  })

  const handleApprove = () => {
    if (confirm(`Send this email to ${draft.lead?.sender_email}?`)) {
      approveMutation.mutate({ action: 'approve', reviewed_by: 'user' })
    }
  }

  const handleReject = () => {
    if (confirm('Reject this draft?')) {
      approveMutation.mutate({ action: 'reject', reviewed_by: 'user' })
    }
  }

  const handleSaveEdits = () => {
    if (!editSummary.trim()) {
      alert('Please provide a summary of your edits')
      return
    }
    saveEditsMutation.mutate()
  }

  const handleSendWithFeedback = (sentiment) => {
    approveMutation.mutate({
      action: 'approve',
      customer_sentiment: sentiment,
      reviewed_by: 'user',
    })
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900">Draft Review</h2>
            <div className="flex items-center gap-3 mt-2">
              <span className={`px-2 py-1 text-xs font-medium rounded ${
                draft.status === 'pending' ? 'bg-blue-100 text-blue-800' :
                draft.status === 'approved' ? 'bg-green-100 text-green-800' :
                draft.status === 'rejected' ? 'bg-red-100 text-red-800' :
                draft.status === 'sent' ? 'bg-purple-100 text-purple-800' :
                'bg-yellow-100 text-yellow-800'
              }`}>
                {draft.status}
              </span>
              <span className="text-sm text-gray-600">
                Confidence: {(draft.confidence_score || 0).toFixed(1)}/10
              </span>
              {draft.lead?.response_priority && (
                <span className={`px-2 py-1 text-xs font-medium rounded border ${
                  draft.lead.response_priority === 'critical' ? 'bg-red-100 text-red-800 border-red-300' :
                  draft.lead.response_priority === 'high' ? 'bg-orange-100 text-orange-800 border-orange-300' :
                  draft.lead.response_priority === 'medium' ? 'bg-yellow-100 text-yellow-800 border-yellow-300' :
                  'bg-gray-100 text-gray-800 border-gray-300'
                }`}>
                  {draft.lead.response_priority} priority
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-2 gap-6 p-6">
            {/* Left Column: Original Lead */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Original Inquiry</h3>

              {/* Lead Info */}
              <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                <div>
                  <label className="text-sm font-medium text-gray-700">From:</label>
                  <p className="text-gray-900">
                    {draft.lead?.sender_name} ({draft.lead?.sender_email})
                  </p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">Subject:</label>
                  <p className="text-gray-900">{draft.lead?.subject}</p>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700">Message:</label>
                  <p className="text-gray-700 whitespace-pre-wrap bg-white rounded p-3 text-sm max-h-64 overflow-y-auto">
                    {draft.lead?.body}
                  </p>
                </div>

                {/* Extracted Data */}
                <div className="border-t border-gray-200 pt-3">
                  <label className="text-sm font-medium text-gray-700">Extracted Data:</label>
                  <div className="mt-2 space-y-2 text-sm">
                    {draft.lead?.product_type && draft.lead.product_type.length > 0 && (
                      <div>
                        <span className="font-medium">Products:</span>{' '}
                        <span className="text-gray-600">{draft.lead.product_type.join(', ')}</span>
                      </div>
                    )}
                    {draft.lead?.certifications_requested && draft.lead.certifications_requested.length > 0 && (
                      <div>
                        <span className="font-medium">Certifications:</span>{' '}
                        <span className="text-gray-600">{draft.lead.certifications_requested.join(', ')}</span>
                      </div>
                    )}
                    {draft.lead?.estimated_quantity && (
                      <div>
                        <span className="font-medium">Quantity:</span>{' '}
                        <span className="text-gray-600">{draft.lead.estimated_quantity}</span>
                      </div>
                    )}
                    {draft.lead?.timeline_urgency && (
                      <div>
                        <span className="font-medium">Timeline:</span>{' '}
                        <span className="text-gray-600">{draft.lead.timeline_urgency}</span>
                      </div>
                    )}
                    <div>
                      <span className="font-medium">Lead Quality:</span>{' '}
                      <span className="text-gray-600">{draft.lead?.lead_quality_score || 'N/A'}/10</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* RAG Sources */}
              {draft.rag_sources && draft.rag_sources.length > 0 && (
                <div className="bg-blue-50 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-blue-900 mb-2">Knowledge Base Sources Used:</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    {draft.rag_sources.map((source, idx) => (
                      <li key={idx} className="flex items-center gap-2">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        {source}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Flags */}
              {draft.flags && draft.flags.length > 0 && (
                <div className="bg-yellow-50 rounded-lg p-4">
                  <h4 className="text-sm font-semibold text-yellow-900 mb-2">⚠️ Flags:</h4>
                  <ul className="text-sm text-yellow-800 space-y-1">
                    {draft.flags.map((flag, idx) => (
                      <li key={idx}>• {flag.replace(/_/g, ' ')}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>

            {/* Right Column: Draft Response */}
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Draft Response</h3>
                {!isEditing && draft.status === 'pending' && (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                  >
                    ✎ Edit Draft
                  </button>
                )}
              </div>

              {/* Subject Line */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Subject:</label>
                {isEditing ? (
                  <input
                    type="text"
                    value={editedSubject}
                    onChange={(e) => setEditedSubject(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                ) : (
                  <p className="text-gray-900 bg-gray-50 rounded p-2">{draft.subject_line}</p>
                )}
              </div>

              {/* Email Body */}
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 mb-1">Message:</label>
                {isEditing ? (
                  <textarea
                    value={editedContent}
                    onChange={(e) => setEditedContent(e.target.value)}
                    rows={16}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                  />
                ) : (
                  <div className="bg-gray-50 rounded-lg p-4 whitespace-pre-wrap text-sm text-gray-900 max-h-96 overflow-y-auto">
                    {draft.draft_content}
                  </div>
                )}
              </div>

              {/* Edit Summary (only when editing) */}
              {isEditing && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Edit Summary (required):</label>
                  <textarea
                    value={editSummary}
                    onChange={(e) => setEditSummary(e.target.value)}
                    rows={2}
                    placeholder="Describe what you changed and why..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                  />
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="border-t border-gray-200 px-6 py-4 bg-gray-50 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Close
          </button>

          {draft.status === 'pending' && (
            <div className="flex items-center gap-3">
              {isEditing ? (
                <>
                  <button
                    onClick={() => {
                      setIsEditing(false)
                      setEditedSubject(draft.subject_line)
                      setEditedContent(draft.draft_content)
                      setEditSummary('')
                    }}
                    className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel Edit
                  </button>
                  <button
                    onClick={handleSaveEdits}
                    disabled={saveEditsMutation.isPending}
                    className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saveEditsMutation.isPending ? 'Saving...' : 'Save Changes'}
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleReject}
                    disabled={approveMutation.isPending}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                  >
                    ✗ Reject
                  </button>
                  <button
                    onClick={handleApprove}
                    disabled={approveMutation.isPending}
                    className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 font-semibold"
                  >
                    {approveMutation.isPending ? 'Sending...' : '✓ Approve & Send'}
                  </button>
                </>
              )}
            </div>
          )}

          {draft.status === 'sent' && (
            <button
              onClick={() => setShowFeedback(!showFeedback)}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Provide Feedback
            </button>
          )}
        </div>

        {/* Feedback Section (for sent emails) */}
        {showFeedback && draft.status === 'sent' && (
          <div className="border-t border-gray-200 px-6 py-4 bg-purple-50">
            <h4 className="font-semibold text-gray-900 mb-3">How did the customer respond?</h4>
            <div className="flex gap-3">
              <button
                onClick={() => handleSendWithFeedback('positive')}
                className="flex-1 px-4 py-3 bg-green-100 text-green-800 rounded-lg hover:bg-green-200 border border-green-300"
              >
                😊 Positive - Engaged/Interested
              </button>
              <button
                onClick={() => handleSendWithFeedback('neutral')}
                className="flex-1 px-4 py-3 bg-gray-100 text-gray-800 rounded-lg hover:bg-gray-200 border border-gray-300"
              >
                😐 Neutral - No Response
              </button>
              <button
                onClick={() => handleSendWithFeedback('negative')}
                className="flex-1 px-4 py-3 bg-red-100 text-red-800 rounded-lg hover:bg-red-200 border border-red-300"
              >
                😞 Negative - Not Interested
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
