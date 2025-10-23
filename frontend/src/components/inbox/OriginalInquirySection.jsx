import { useState } from 'react'

export default function OriginalInquirySection({ lead }) {
  const [isExpanded, setIsExpanded] = useState(true)

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-5 hover:bg-gray-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg
            className={`w-5 h-5 text-gray-600 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900">
            Original Inquiry from {lead?.sender_name || 'Unknown'}
          </h3>
        </div>
        <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
        </svg>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="p-6 pt-0 space-y-5">
          {/* Sender Info Card */}
          <div className="bg-white border border-gray-200 rounded-lg p-5 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">From</label>
                <p className="text-sm text-gray-900 font-medium">{lead?.sender_name || 'Unknown'}</p>
              </div>
              <div>
                <label className="text-xs font-medium text-gray-500 uppercase">Email</label>
                <p className="text-sm text-gray-900">{lead?.sender_email}</p>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">Subject</label>
              <p className="text-sm text-gray-900 font-medium">{lead?.subject}</p>
            </div>

            <div>
              <label className="text-xs font-medium text-gray-500 uppercase">Received</label>
              <p className="text-sm text-gray-900">
                {lead?.created_at ? new Date(lead.created_at).toLocaleString() : 'N/A'}
              </p>
            </div>
          </div>

          {/* Original Message */}
          <div>
            <label className="block text-xs font-medium text-gray-500 uppercase mb-2">Message</label>
            <div className="bg-white border border-gray-200 rounded-lg p-5 max-h-80 overflow-y-auto">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">
                {lead?.body || 'No message content available'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
