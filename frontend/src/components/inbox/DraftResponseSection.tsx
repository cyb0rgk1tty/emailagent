import { useState, ChangeEvent, Dispatch, SetStateAction } from 'react';
import type { Draft } from '../../types/api';

interface DraftResponseSectionProps {
  draft: Draft;
  isEditMode: boolean;
  editedSubject: string;
  setEditedSubject: Dispatch<SetStateAction<string>>;
  editedContent: string;
  setEditedContent: Dispatch<SetStateAction<string>>;
  editSummary: string;
  setEditSummary: Dispatch<SetStateAction<string>>;
}

export default function DraftResponseSection({
  draft,
  isEditMode,
  editedSubject,
  setEditedSubject,
  editedContent,
  setEditedContent,
  editSummary,
  setEditSummary,
}: DraftResponseSectionProps): JSX.Element {
  const [showRagSources, setShowRagSources] = useState(false);

  return (
    <div className="bg-white border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-gray-200 p-5">
        <div className="flex items-center gap-2">
          <svg className="w-5 h-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900">Your Draft Response</h3>
          {isEditMode && (
            <span className="ml-auto px-2 py-1 bg-blue-100 text-blue-700 text-xs font-medium rounded">
              Editing Mode
            </span>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-8 space-y-6">
        {/* Subject Line */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Subject
          </label>
          {isEditMode ? (
            <input
              type="text"
              value={editedSubject}
              onChange={(e: ChangeEvent<HTMLInputElement>) => setEditedSubject(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-medium"
              placeholder="Email subject..."
            />
          ) : (
            <div className="px-4 py-2 bg-gray-50 border border-gray-200 rounded-lg font-medium text-gray-900">
              {draft.subject_line}
            </div>
          )}
        </div>

        {/* Email Body */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Message
          </label>
          {isEditMode ? (
            <textarea
              value={editedContent}
              onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setEditedContent(e.target.value)}
              rows={20}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm resize-none"
              placeholder="Email content..."
            />
          ) : (
            <div className="px-5 py-4 bg-gray-50 border border-gray-200 rounded-lg whitespace-pre-wrap text-sm text-gray-900 min-h-[450px] max-h-[700px] overflow-y-auto leading-relaxed">
              {draft.draft_content}
            </div>
          )}
        </div>

        {/* Edit Summary (only shown in edit mode) */}
        {isEditMode && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <label className="block text-sm font-medium text-yellow-900 mb-2">
              Edit Summary (required)
            </label>
            <textarea
              value={editSummary}
              onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setEditSummary(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent text-sm"
              placeholder="Describe what you changed and why (e.g., 'Fixed typo in pricing section' or 'Made tone more professional')..."
            />
          </div>
        )}

        {/* RAG Sources (Collapsible) */}
        {draft.rag_sources && draft.rag_sources.length > 0 && (
          <div className="border-t border-gray-200 pt-4">
            <button
              onClick={() => setShowRagSources(!showRagSources)}
              className="flex items-center gap-2 text-sm font-semibold text-gray-900 hover:text-blue-600 transition-colors"
            >
              <svg
                className={`w-4 h-4 transition-transform ${showRagSources ? 'rotate-90' : ''}`}
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Knowledge Base Sources Used ({draft.rag_sources.length})
            </button>

            {showRagSources && (
              <div className="mt-3 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <ul className="space-y-2">
                  {draft.rag_sources.map((source, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-blue-800">
                      <svg className="w-4 h-4 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span>{source}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Flags/Warnings */}
        {draft.flags && draft.flags.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <div className="flex-1">
                <h4 className="text-sm font-semibold text-yellow-900 mb-1">Flags & Warnings</h4>
                <ul className="text-sm text-yellow-800 space-y-1">
                  {draft.flags.map((flag, idx) => (
                    <li key={idx}>- {flag.replace(/_/g, ' ')}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
