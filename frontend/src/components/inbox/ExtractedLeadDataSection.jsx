import { useState } from 'react'

export default function ExtractedLeadDataSection({ lead }) {
  const [isExpanded, setIsExpanded] = useState(false)

  // Helper function to capitalize first letter of each word
  const capitalizeText = (text) => {
    if (!text) return text
    return text.split(' ').map(word =>
      word.charAt(0).toUpperCase() + word.slice(1).toLowerCase()
    ).join(' ')
  }

  if (!lead) return null

  const hasData = lead?.product_type?.length > 0 ||
    lead?.certifications_requested?.length > 0 ||
    lead?.delivery_format?.length > 0 ||
    lead?.estimated_quantity ||
    lead?.timeline_urgency ||
    lead?.experience_level ||
    lead?.response_priority

  if (!hasData) return null

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-5 hover:bg-blue-100 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg
            className={`w-5 h-5 text-blue-600 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <h3 className="text-lg font-semibold text-blue-900">
            Extracted Lead Intelligence
          </h3>
        </div>
        <span className="text-sm text-blue-700 font-medium">
          Quality Score: {lead?.lead_quality_score || 'N/A'}/10
        </span>
      </button>

      {/* Content */}
      {isExpanded && (
        <div className="px-6 pb-6 pt-2">
          <div className="bg-white border border-blue-200 rounded-lg p-5 space-y-4 text-sm">
            {lead?.product_type && lead.product_type.length > 0 && (
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">Products:</span>{' '}
                  <span className="text-gray-700">{lead.product_type.map(capitalizeText).join(', ')}</span>
                </div>
              </div>
            )}
            {lead?.certifications_requested && lead.certifications_requested.length > 0 && (
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">Certifications:</span>{' '}
                  <span className="text-gray-700">{lead.certifications_requested.map(capitalizeText).join(', ')}</span>
                </div>
              </div>
            )}
            {lead?.delivery_format && lead.delivery_format.length > 0 && (
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                </svg>
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">Delivery Format:</span>{' '}
                  <span className="text-gray-700">{lead.delivery_format.map(capitalizeText).join(', ')}</span>
                </div>
              </div>
            )}
            {lead?.estimated_quantity && (
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
                </svg>
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">Estimated Quantity:</span>{' '}
                  <span className="text-gray-700">{capitalizeText(lead.estimated_quantity)}</span>
                </div>
              </div>
            )}
            {lead?.timeline_urgency && (
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">Timeline:</span>{' '}
                  <span className="text-gray-700">{capitalizeText(lead.timeline_urgency)}</span>
                </div>
              </div>
            )}
            {lead?.experience_level && (
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">Experience Level:</span>{' '}
                  <span className="text-gray-700">{capitalizeText(lead.experience_level)}</span>
                </div>
              </div>
            )}
            {lead?.response_priority && (
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div className="flex-1">
                  <span className="font-semibold text-gray-900">Response Priority:</span>{' '}
                  <span className={`font-medium ${
                    lead.response_priority === 'critical' ? 'text-red-700' :
                    lead.response_priority === 'high' ? 'text-orange-700' :
                    lead.response_priority === 'medium' ? 'text-yellow-700' :
                    'text-gray-700'
                  }`}>
                    {capitalizeText(lead.response_priority)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
